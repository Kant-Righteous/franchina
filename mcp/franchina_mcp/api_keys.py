"""Multi-user API key authentication for the FranChina MCP.

``FRANCHINA_MCP_MODE=api-key`` authenticates public requests with per-user
bearer keys that exist only in a dedicated auth database, fully separate from
the exchange-rate data. Keys are never configured through Git, environment
variables, or the deployment workflow: they are created on the server shell
with ``python -m franchina_mcp.keys``. The plaintext key is printed exactly
once at creation; the database stores only the key id and a SHA-256 digest of
the 256-bit CSPRNG secret, compared in constant time.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import sqlite3
from collections.abc import Iterable
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server.transport_security import DEFAULT_MAX_REQUEST_BODY_SIZE

from .public_gate import header_value, is_loopback_host, send_json_error

logger = logging.getLogger(__name__)

API_KEY_PREFIX = "fmcp_"
KEY_ID_BYTES = 8  # 16 hex characters
SECRET_BYTES = 32  # 256-bit CSPRNG secret, hex-encoded to 64 characters
RATES_WRITE_SCOPE = "rates:write"

# Scopes required per MCP tool. Tools without an entry are treated as
# read-only and need nothing beyond a valid key; write tools must be listed
# here explicitly so they can never be reached with a lesser scope.
TOOL_SCOPES: dict[str, tuple[str, ...]] = {
    "save_exchange_rates": (RATES_WRITE_SCOPE,),
}

CREATE_API_KEYS_SQL = """
CREATE TABLE IF NOT EXISTS api_keys (
    key_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    scopes TEXT NOT NULL DEFAULT '',
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
    created_at TEXT NOT NULL,
    expires_at TEXT,
    last_used_at TEXT
)
"""


class ApiKeyError(Exception):
    """A presented bearer key failed authentication.

    The message is meant for server-side logs only; clients always receive a
    uniform 401 so failures cannot be told apart from the outside.
    """


@dataclass(frozen=True, slots=True)
class ApiKeyRecord:
    key_id: str
    name: str
    key_hash: str
    scopes: frozenset[str]
    enabled: bool
    created_at: str
    expires_at: str | None
    last_used_at: str | None

    @property
    def scope_display(self) -> str:
        return " ".join(sorted(self.scopes)) or "(none)"


def hash_secret(secret: str) -> str:
    # A fixed fast digest is acceptable because the secret is a 256-bit
    # CSPRNG value (not a low-entropy password), and the comparison in
    # ApiKeyAuthenticator runs in constant time over the digest.
    return hashlib.sha256(secret.encode("ascii")).hexdigest()


def parse_api_key(presented: str) -> tuple[str, str]:
    """Split ``fmcp_<key_id>_<secret>``; raises ApiKeyError when malformed."""
    if not presented.startswith(API_KEY_PREFIX):
        raise ApiKeyError("missing fmcp_ prefix")
    key_id, separator, secret = presented[len(API_KEY_PREFIX) :].partition("_")
    if not key_id or not separator or not secret:
        raise ApiKeyError("malformed key")
    return key_id, secret


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    )


def _parse_timestamp(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("expires_at must include a timezone")
    utc_value = value.astimezone(timezone.utc)
    return utc_value.isoformat(timespec="seconds").replace("+00:00", "Z")


def _row_to_record(row: sqlite3.Row) -> ApiKeyRecord:
    return ApiKeyRecord(
        key_id=row["key_id"],
        name=row["name"],
        key_hash=row["key_hash"],
        scopes=frozenset(row["scopes"].split()),
        enabled=bool(row["enabled"]),
        created_at=row["created_at"],
        expires_at=row["expires_at"],
        last_used_at=row["last_used_at"],
    )


class ApiKeyRepository:
    """Dedicated auth database; deliberately independent of the rates store."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
            isolation_level=None,
        )
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        # IF NOT EXISTS keeps existing keys intact: reopening the database
        # (deployments, restarts) never resets credentials.
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            connection.execute(CREATE_API_KEYS_SQL)

    def create(
        self,
        *,
        name: str,
        scopes: Iterable[str] = (),
        expires_at: datetime | None = None,
    ) -> tuple[ApiKeyRecord, str]:
        """Create a key and return (record, plaintext key shown once)."""
        name = name.strip()
        if not name:
            raise ValueError("key name cannot be empty")
        scope_text = " ".join(sorted(set(scopes)))
        expires_text = _format_timestamp(expires_at) if expires_at else None
        created_at = _utc_now_iso()

        for _ in range(5):
            key_id = secrets.token_hex(KEY_ID_BYTES)
            secret = secrets.token_hex(SECRET_BYTES)
            key_hash = hash_secret(secret)
            try:
                with closing(self._connect()) as connection:
                    connection.execute(
                        """
                        INSERT INTO api_keys (
                            key_id, name, key_hash, scopes, enabled,
                            created_at, expires_at, last_used_at
                        ) VALUES (?, ?, ?, ?, 1, ?, ?, NULL)
                        """,
                        (key_id, name, key_hash, scope_text, created_at, expires_text),
                    )
            except sqlite3.IntegrityError:
                continue  # key id collision; retry with fresh entropy
            record = ApiKeyRecord(
                key_id=key_id,
                name=name,
                key_hash=key_hash,
                scopes=frozenset(scope_text.split()),
                enabled=True,
                created_at=created_at,
                expires_at=expires_text,
                last_used_at=None,
            )
            return record, f"{API_KEY_PREFIX}{key_id}_{secret}"
        raise RuntimeError("failed to allocate a unique key id")

    def find(self, key_id: str) -> ApiKeyRecord | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM api_keys WHERE key_id = ?", (key_id,)
            ).fetchone()
        return _row_to_record(row) if row is not None else None

    def list_keys(self) -> list[ApiKeyRecord]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM api_keys ORDER BY created_at, key_id"
            ).fetchall()
        return [_row_to_record(row) for row in rows]

    def set_enabled(self, key_id: str, enabled: bool) -> bool:
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                "UPDATE api_keys SET enabled = ? WHERE key_id = ?",
                (1 if enabled else 0, key_id),
            )
        return cursor.rowcount > 0

    def revoke(self, key_id: str) -> bool:
        return self.set_enabled(key_id, enabled=False)

    def touch(self, key_id: str) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                "UPDATE api_keys SET last_used_at = ? WHERE key_id = ?",
                (_utc_now_iso(), key_id),
            )


class ApiKeyAuthenticator:
    """Verifies bearer keys against the repository, fail closed."""

    def __init__(self, repository: ApiKeyRepository) -> None:
        self.repository = repository

    def authenticate(self, presented: str) -> ApiKeyRecord:
        key_id, secret = parse_api_key(presented)
        record = self.repository.find(key_id)
        if record is None:
            raise ApiKeyError("unknown key")
        if not hmac.compare_digest(record.key_hash, hash_secret(secret)):
            raise ApiKeyError("secret mismatch")
        if not record.enabled:
            raise ApiKeyError("key disabled")
        if record.expires_at is not None:
            expiry = _parse_timestamp(record.expires_at)
            if expiry is None or datetime.now(timezone.utc) >= expiry:
                raise ApiKeyError("key expired")
        return record

    def record_usage(self, key_id: str) -> None:
        try:
            self.repository.touch(key_id)
        except sqlite3.Error as error:
            logger.warning("Failed to update last_used_at: %s", error)


async def _buffer_request_body(receive: Any, limit: int) -> tuple[bytes, bool]:
    chunks: list[bytes] = []
    total = 0
    while True:
        message = await receive()
        if message["type"] == "http.disconnect":
            return b"", False
        if message["type"] != "http.request":
            continue
        total += len(message.get("body", b""))
        if total > limit:
            return b"", False
        chunks.append(message.get("body", b""))
        if not message.get("more_body", False):
            break
    return b"".join(chunks), True


def _replay_body(receive: Any, body: bytes) -> Any:
    pending = [{"type": "http.request", "body": body, "more_body": False}]

    async def replay() -> dict[str, Any]:
        if pending:
            return pending.pop(0)
        return await receive()

    return replay


def missing_tool_scope(raw_body: bytes, scopes: frozenset[str]) -> str | None:
    """Return the first tool scope the key lacks, or None if all are covered.

    Only ``tools/call`` requests are inspected. Malformed bodies impose no
    restriction here; the MCP layer rejects them on its own.
    """
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    messages = payload if isinstance(payload, list) else [payload]
    for message in messages:
        if not isinstance(message, dict) or message.get("method") != "tools/call":
            continue
        params = message.get("params")
        tool_name = params.get("name") if isinstance(params, dict) else None
        for required in TOOL_SCOPES.get(tool_name, ()):
            if required not in scopes:
                return required
    return None


class ApiKeyMiddleware:
    """Pure ASGI gate enforcing bearer keys and per-tool scopes in public mode.

    Public traffic (any non-loopback Host) must authenticate on every path;
    loopback traffic only on the MCP endpoint itself, so the systemd health
    check against ``127.0.0.1:8765/health`` keeps working. Failed
    authentication is a uniform 401; a valid key lacking a tool's scope gets
    403. Neither the key nor the Authorization header is ever logged.
    """

    def __init__(
        self,
        app: Any,
        authenticator: ApiKeyAuthenticator,
        *,
        protected_paths: tuple[str, ...] = ("/mcp",),
        max_request_body_bytes: int = DEFAULT_MAX_REQUEST_BODY_SIZE,
    ) -> None:
        self.app = app
        self.authenticator = authenticator
        self.protected_paths = protected_paths
        self.max_request_body_bytes = max_request_body_bytes

    def requires_authentication(self, *, path: str, host: str) -> bool:
        if is_loopback_host(host):
            return path in self.protected_paths
        return True

    @staticmethod
    def _extract_bearer_token(scope: dict[str, Any]) -> str | None:
        authorization = header_value(scope, b"authorization")
        if authorization is None:
            return None
        scheme, _, token = authorization.partition(" ")
        token = token.strip()
        if scheme.lower() != "bearer" or not token:
            return None
        return token

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        host = header_value(scope, b"host") or ""
        path = scope.get("path") or "/"
        if not self.requires_authentication(path=path, host=host):
            await self.app(scope, receive, send)
            return

        presented = self._extract_bearer_token(scope)
        if presented is None:
            logger.warning(
                "Rejected %s request to host %r without a bearer API key", path, host
            )
            await send_json_error(send, 401, {"error": "unauthorized"})
            return

        try:
            record = self.authenticator.authenticate(presented)
        except ApiKeyError as error:
            logger.warning("Rejected API key for %s (host %r): %s", path, host, error)
            await send_json_error(send, 401, {"error": "unauthorized"})
            return

        if scope["method"] == "POST" and path in self.protected_paths:
            body, buffered = await _buffer_request_body(
                receive, self.max_request_body_bytes
            )
            if not buffered:
                await send_json_error(send, 413, {"error": "payload too large"})
                return
            missing_scope = missing_tool_scope(body, record.scopes)
            if missing_scope is not None:
                logger.warning(
                    "Rejected tool call on %s: key lacks required scope %r",
                    path,
                    missing_scope,
                )
                await send_json_error(send, 403, {"error": "insufficient_scope"})
                return
            receive = _replay_body(receive, body)

        self.authenticator.record_usage(record.key_id)
        await self.app(scope, receive, send)
