"""Cloudflare Access Managed OAuth origin-side validation.

In public mode the service sits behind Cloudflare Access: the edge terminates
the OAuth flow for ``mcp.franchina.qzz.io`` and forwards authenticated requests
to the origin with a signed ``Cf-Access-Jwt-Assertion`` header. This module
resolves the production configuration from environment variables, fetches the
team's public JWKS from ``/cdn-cgi/access/certs``, and cryptographically
verifies every assertion. It deliberately implements only the relying-party
side; the OAuth Authorization Server lives at the Cloudflare edge.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import jwt
from jwt import PyJWK
from jwt.exceptions import InvalidTokenError

logger = logging.getLogger(__name__)

MODE_ENV = "FRANCHINA_MCP_MODE"
TEAM_DOMAIN_ENV = "FRANCHINA_MCP_CF_TEAM_DOMAIN"
APPLICATION_AUD_ENV = "FRANCHINA_MCP_CF_APPLICATION_AUD"

LOOPBACK_MODE = "loopback"
CLOUDFLARE_ACCESS_MODE = "cloudflare-access"

ACCESS_CERTS_PATH = "/cdn-cgi/access/certs"
ASSERTION_HEADER = "Cf-Access-Jwt-Assertion"
ASSERTION_HEADER_BYTES = ASSERTION_HEADER.encode("ascii").lower()
ACCESS_JWT_ALGORITHM = "RS256"
REQUIRED_CLAIMS = ("exp", "aud", "iss", "sub")
TEAM_HOSTNAME_PATTERN = re.compile(r"[a-z0-9-]+(?:\.[a-z0-9-]+)+")

# The Host values this origin accepts for machine-local traffic (the systemd
# deployment health check and cloudflared on the same host). Everything else
# counts as public traffic and always requires an Access assertion.
LOOPBACK_HOSTNAMES = frozenset({"127.0.0.1", "localhost", "::1"})

JwksFetcher = Callable[[str], Mapping[str, Any]]


class AccessConfigurationError(RuntimeError):
    """Public mode configuration is missing or invalid; startup must fail."""


class AccessAssertionError(Exception):
    """A presented Cf-Access-Jwt-Assertion failed cryptographic validation."""


class AccessJwksError(Exception):
    """The Cloudflare Access JWKS could not be loaded."""


@dataclass(frozen=True, slots=True)
class CloudflareAccessSettings:
    """Resolved Cloudflare Access configuration. No secret values involved."""

    team_url: str
    application_aud: str

    @property
    def issuer(self) -> str:
        return self.team_url

    @property
    def certs_url(self) -> str:
        return self.team_url + ACCESS_CERTS_PATH

    @classmethod
    def from_env(
        cls, environ: Mapping[str, str] | None = None
    ) -> CloudflareAccessSettings:
        environment = os.environ if environ is None else environ
        missing = [
            name
            for name in (TEAM_DOMAIN_ENV, APPLICATION_AUD_ENV)
            if not str(environment.get(name, "")).strip()
        ]
        if missing:
            raise AccessConfigurationError(
                f"{CLOUDFLARE_ACCESS_MODE} mode requires environment variables "
                f"{TEAM_DOMAIN_ENV} and {APPLICATION_AUD_ENV}; missing: {', '.join(missing)}"
            )

        team_url = _normalize_team_domain(environment[TEAM_DOMAIN_ENV])
        application_aud = environment[APPLICATION_AUD_ENV].strip()
        if any(character.isspace() for character in application_aud):
            raise AccessConfigurationError(
                f"{APPLICATION_AUD_ENV} must be a single Access Application AUD tag"
            )
        return cls(team_url=team_url, application_aud=application_aud)


def _normalize_team_domain(raw: str) -> str:
    value = raw.strip()
    if not value:
        raise AccessConfigurationError(f"{TEAM_DOMAIN_ENV} cannot be empty")
    if "://" not in value:
        value = f"https://{value}"

    try:
        parsed = urlsplit(value)
    except ValueError as error:
        raise AccessConfigurationError(
            f"{TEAM_DOMAIN_ENV} is not a valid URL: {raw!r}"
        ) from error

    if parsed.scheme != "https" or not parsed.hostname:
        raise AccessConfigurationError(
            f"{TEAM_DOMAIN_ENV} must be an https Cloudflare team domain, got: {raw!r}"
        )
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise AccessConfigurationError(
            f"{TEAM_DOMAIN_ENV} must not contain a path, query, or fragment: {raw!r}"
        )
    try:
        port = parsed.port
    except ValueError as error:
        raise AccessConfigurationError(
            f"{TEAM_DOMAIN_ENV} is not a valid URL: {raw!r}"
        ) from error
    if port not in (None, 443):
        raise AccessConfigurationError(
            f"{TEAM_DOMAIN_ENV} must not include a port: {raw!r}"
        )
    hostname = parsed.hostname.lower()
    if not TEAM_HOSTNAME_PATTERN.fullmatch(hostname):
        raise AccessConfigurationError(
            f"{TEAM_DOMAIN_ENV} is not a valid Cloudflare team domain: {raw!r}"
        )

    return f"https://{hostname}"


def resolve_run_mode(environ: Mapping[str, str] | None = None) -> str:
    environment = os.environ if environ is None else environ
    raw = str(environment.get(MODE_ENV, "")).strip()
    if not raw or raw == LOOPBACK_MODE:
        return LOOPBACK_MODE
    if raw == CLOUDFLARE_ACCESS_MODE:
        return CLOUDFLARE_ACCESS_MODE
    raise SystemExit(
        f"{MODE_ENV} must be '{LOOPBACK_MODE}' or '{CLOUDFLARE_ACCESS_MODE}', got: {raw!r}"
    )


def _fetch_jwks_document(certs_url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        certs_url, headers={"Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=10.0) as response:
            document = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError) as error:
        raise AccessJwksError(
            f"Failed to load Cloudflare Access JWKS from {certs_url}: {error}"
        ) from error
    if not isinstance(document, dict) or not isinstance(document.get("keys"), list):
        raise AccessJwksError(
            f"Cloudflare Access JWKS at {certs_url} has no 'keys' array"
        )
    return document


class CloudflareAccessJwks:
    """Signing keys from the team's public certs endpoint, cached by key id.

    Unknown key ids trigger a rate-limited reload so Cloudflare key rotation
    converges without letting attackers hammer the endpoint.
    """

    def __init__(
        self,
        certs_url: str,
        *,
        fetch: JwksFetcher | None = None,
        min_refresh_interval: float = 60.0,
        cache_ttl: float = 3600.0,
    ) -> None:
        self._certs_url = certs_url
        self._fetch = fetch or _fetch_jwks_document
        self._min_refresh_interval = min_refresh_interval
        self._cache_ttl = cache_ttl
        self._keys: dict[str, PyJWK] = {}
        self._last_load: float | None = None

    def load(self) -> None:
        document = self._fetch(self._certs_url)
        keys: dict[str, PyJWK] = {}
        for entry in document["keys"]:
            if not isinstance(entry, dict):
                continue
            kid = entry.get("kid")
            if not isinstance(kid, str) or not kid:
                continue
            keys[kid] = PyJWK(entry, algorithm=ACCESS_JWT_ALGORITHM)
        if not keys:
            raise AccessJwksError(
                f"Cloudflare Access JWKS at {self._certs_url} contains no usable keys"
            )
        self._keys = keys
        self._last_load = time.monotonic()
        logger.info(
            "Loaded %d Cloudflare Access signing key(s) from %s",
            len(keys),
            self._certs_url,
        )

    def _refresh(self, now: float, *, force: bool) -> None:
        if self._last_load is None:
            if force:
                self.load()
            return
        since_last_load = now - self._last_load
        if since_last_load < self._min_refresh_interval:
            return
        try:
            self.load()
        except AccessJwksError as error:
            logger.warning("Cloudflare Access JWKS refresh failed: %s", error)

    def get_signing_key(self, kid: str) -> PyJWK | None:
        key = self._keys.get(kid)
        if key is not None:
            now = time.monotonic()
            if (
                self._last_load is not None
                and now - self._last_load >= self._cache_ttl
            ):
                self._refresh(now, force=False)
            return key
        self._refresh(time.monotonic(), force=True)
        return self._keys.get(kid)


class CloudflareAccessValidator:
    """Cryptographic validation of Cloudflare Access JWT assertions."""

    def __init__(
        self,
        settings: CloudflareAccessSettings,
        *,
        jwks: CloudflareAccessJwks | None = None,
    ) -> None:
        self.settings = settings
        self.jwks = jwks or CloudflareAccessJwks(settings.certs_url)
        # Fail fast: a public-mode origin must never start without the keys it
        # needs to authenticate requests.
        self.jwks.load()
        logger.info(
            "Cloudflare Access assertion validation enabled (issuer=%s)",
            settings.issuer,
        )

    def verify_assertion(self, token: str) -> dict[str, Any]:
        """Validate an assertion and return its claims.

        Raises AccessAssertionError for every rejection path: malformed token,
        unknown key, bad signature, wrong audience or issuer, or time window
        violations. Callers must not distinguish these externally.
        """
        try:
            header = jwt.get_unverified_header(token)
        except InvalidTokenError as error:
            raise AccessAssertionError(f"malformed assertion: {error}") from error

        kid = header.get("kid")
        if header.get("alg") != ACCESS_JWT_ALGORITHM or not isinstance(kid, str):
            raise AccessAssertionError("assertion must be RS256 with a key id")

        signing_key = self.jwks.get_signing_key(kid)
        if signing_key is None:
            raise AccessAssertionError(f"unknown signing key id: {kid}")

        try:
            claims = jwt.decode(
                token,
                key=signing_key.key,
                algorithms=[ACCESS_JWT_ALGORITHM],
                audience=self.settings.application_aud,
                options={"require": list(REQUIRED_CLAIMS)},
                leeway=0,
            )
        except InvalidTokenError as error:
            raise AccessAssertionError(f"invalid assertion: {error}") from error

        # Issuer is compared manually so that a trailing slash on either side
        # (Cloudflare emits `https://<team>.cloudflareaccess.com`) cannot cause
        # a spurious mismatch, while any real difference is rejected.
        if claims.get("iss", "").rstrip("/") != self.settings.issuer:
            raise AccessAssertionError(
                f"assertion issuer does not match {self.settings.issuer}"
            )
        return claims


def is_loopback_host(host: str) -> bool:
    if not host:
        return False
    try:
        hostname = urlsplit(f"//{host}").hostname
    except ValueError:
        return False
    return hostname is not None and hostname.lower() in LOOPBACK_HOSTNAMES


def _header_value(scope: dict[str, Any], name_bytes: bytes) -> str | None:
    for key, value in scope.get("headers", []):
        if key.lower() == name_bytes:
            return value.decode("latin-1")
    return None


async def _send_unauthorized(send: Any) -> None:
    body = b'{"error":"unauthorized"}'
    await send(
        {
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
                (b"cache-control", b"no-store"),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


class CloudflareAccessMiddleware:
    """Pure ASGI gate that enforces Access assertions in public mode.

    Public traffic (any non-loopback Host) requires a valid assertion on every
    path. Loopback traffic only needs one on the MCP endpoint itself, so the
    systemd deployment health check against ``127.0.0.1:8765/health`` keeps
    working unchanged. Implemented as raw ASGI so streamable HTTP/SSE
    responses pass through untouched.
    """

    def __init__(
        self,
        app: Any,
        validator: CloudflareAccessValidator,
        *,
        protected_paths: tuple[str, ...] = ("/mcp",),
    ) -> None:
        self.app = app
        self.validator = validator
        self.protected_paths = protected_paths

    def requires_assertion(self, *, path: str, host: str) -> bool:
        if is_loopback_host(host):
            return path in self.protected_paths
        return True

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        host = _header_value(scope, b"host") or ""
        path = scope.get("path") or "/"
        if not self.requires_assertion(path=path, host=host):
            await self.app(scope, receive, send)
            return

        assertion = _header_value(scope, ASSERTION_HEADER_BYTES)
        if assertion is None:
            logger.warning(
                "Rejected %s request to host %r without %s header",
                path,
                host,
                ASSERTION_HEADER,
            )
            await _send_unauthorized(send)
            return

        try:
            self.validator.verify_assertion(assertion)
        except AccessAssertionError as error:
            logger.warning(
                "Rejected Access assertion for %s (host %r): %s", path, host, error
            )
            await _send_unauthorized(send)
            return

        await self.app(scope, receive, send)
