from __future__ import annotations

import json
import sqlite3
import time
import unittest
from collections.abc import Callable
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from mcp.server.auth.settings import AuthSettings
from starlette.testclient import TestClient

from franchina_mcp import cloudflare_access as access_module
from franchina_mcp import server as server_module
from franchina_mcp.database import RatesRepository

TEAM_URL = "https://franchina-test.cloudflareaccess.com"
APPLICATION_AUD = "e0c9bbbb1b0f4e22b85f1234567890ab"
LEGIT_KID = "legit-access-key"
ROTATED_KID = "rotated-access-key"
PUBLIC_HOST = "mcp.franchina.qzz.io"
ACCEPT_SSE = {"accept": "application/json, text/event-stream"}

VALID_RATE = {
    "date": "2026-09-02",
    "source": "European Central Bank",
    "currency": "EUR",
    "rate_type": "reference",
    "rate": "7.8633",
    "source_url": "https://example.com/rates",
}


def generate_private_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def build_jwk(private_key: rsa.RSAPrivateKey, kid: str) -> dict[str, Any]:
    jwk = json.loads(pyjwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk.update(kid=kid, alg="RS256", use="sig")
    return jwk


class RecordingFetcher:
    """JWKS fetcher double: returns a fresh document on every call."""

    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []
        self.urls: list[str] = []
        self.calls = 0

    def push(self, document: dict[str, Any]) -> None:
        self.documents.append(document)

    def __call__(self, url: str) -> dict[str, Any]:
        self.calls += 1
        self.urls.append(url)
        return self.documents[min(self.calls - 1, len(self.documents) - 1)]


def create_validator(
    *,
    fetch: Callable[[str], dict[str, Any]] | None = None,
    jwks_document: dict[str, Any] | None = None,
    min_refresh_interval: float = 60.0,
) -> access_module.CloudflareAccessValidator:
    if fetch is None:
        fetcher = RecordingFetcher()
        fetcher.push(jwks_document or {"keys": [build_jwk(LEGIT_KEY, LEGIT_KID)]})
        fetch = fetcher
    settings = access_module.CloudflareAccessSettings(
        team_url=TEAM_URL,
        application_aud=APPLICATION_AUD,
    )
    return access_module.CloudflareAccessValidator(
        settings,
        jwks=access_module.CloudflareAccessJwks(
            settings.certs_url,
            fetch=fetch,
            min_refresh_interval=min_refresh_interval,
        ),
    )


def issue_token(
    private_key: Any,
    *,
    kid: str = LEGIT_KID,
    algorithm: str = "RS256",
    audience: Any = APPLICATION_AUD,
    issuer: str = TEAM_URL,
    expires_in: int = 600,
    not_before: int | None = None,
    without_claims: tuple[str, ...] = (),
) -> str:
    now = int(time.time())
    claims: dict[str, Any] = {
        "iss": issuer,
        "aud": audience,
        "sub": "user@example.com",
        "iat": now,
        "exp": now + expires_in,
        "email": "user@example.com",
    }
    if not_before is not None:
        claims["nbf"] = not_before
    for claim in without_claims:
        claims.pop(claim, None)
    return pyjwt.encode(
        claims, private_key, algorithm=algorithm, headers={"kid": kid}
    )


def parse_sse_message(payload: str) -> dict[str, Any]:
    for line in reversed(payload.splitlines()):
        if line.startswith("data:"):
            return json.loads(line.removeprefix("data:").strip())
    raise AssertionError(f"no SSE data message in response: {payload!r}")


LEGIT_KEY = generate_private_key()
ATTACKER_KEY = generate_private_key()
ROTATED_KEY = generate_private_key()
LEGIT_JWKS = {"keys": [build_jwk(LEGIT_KEY, LEGIT_KID)]}


def create_public_client(
    validator: access_module.CloudflareAccessValidator,
    *,
    repository: RatesRepository | None = None,
) -> TestClient:
    server = server_module.create_server(
        repository, public=True, access_validator=validator
    )
    app = server_module.create_streamable_http_app(
        server,
        access_validator=validator,
        public=True,
        stateless_http=True,
    )
    return TestClient(app, base_url="http://127.0.0.1:8765")


def initialize_streamable_http(client: TestClient, headers: dict[str, str]) -> None:
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "access-test", "version": "0.0.0"},
            },
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text
    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        headers=headers,
    )
    assert response.status_code == 202, response.text


class CloudflareAccessSettingsTests(unittest.TestCase):
    def test_missing_environment_variables_fail_with_explicit_names(self) -> None:
        with self.assertRaises(access_module.AccessConfigurationError) as context:
            access_module.CloudflareAccessSettings.from_env(environ={})

        message = str(context.exception)
        self.assertIn(access_module.TEAM_DOMAIN_ENV, message)
        self.assertIn(access_module.APPLICATION_AUD_ENV, message)

    def test_missing_application_aud_alone_fails(self) -> None:
        with self.assertRaises(access_module.AccessConfigurationError):
            access_module.CloudflareAccessSettings.from_env(
                environ={access_module.TEAM_DOMAIN_ENV: TEAM_URL}
            )

    def test_bare_team_domain_is_normalized_to_https(self) -> None:
        settings = access_module.CloudflareAccessSettings.from_env(
            environ={
                access_module.TEAM_DOMAIN_ENV: "Franchina-Test.cloudflareaccess.com/",
                access_module.APPLICATION_AUD_ENV: APPLICATION_AUD,
            }
        )
        self.assertEqual(settings.team_url, TEAM_URL)
        self.assertEqual(settings.issuer, TEAM_URL)
        self.assertEqual(
            settings.certs_url, TEAM_URL + access_module.ACCESS_CERTS_PATH
        )

    def test_rejects_non_https_path_or_fragment_team_domains(self) -> None:
        for raw in (
            "http://franchina-test.cloudflareaccess.com",
            "https://franchina-test.cloudflareaccess.com/some/path",
            "https://franchina-test.cloudflareaccess.com?x=1",
            "https://franchina-test.cloudflareaccess.com#frag",
            "   ",
            "not a url",
        ):
            with (
                self.subTest(raw=raw),
                self.assertRaises(access_module.AccessConfigurationError),
            ):
                access_module.CloudflareAccessSettings.from_env(
                    environ={
                        access_module.TEAM_DOMAIN_ENV: raw,
                        access_module.APPLICATION_AUD_ENV: APPLICATION_AUD,
                    }
                )

    def test_rejects_application_aud_with_whitespace(self) -> None:
        with self.assertRaises(access_module.AccessConfigurationError):
            access_module.CloudflareAccessSettings.from_env(
                environ={
                    access_module.TEAM_DOMAIN_ENV: TEAM_URL,
                    access_module.APPLICATION_AUD_ENV: "aud with spaces",
                }
            )


class ValidatorStartupTests(unittest.TestCase):
    def test_validator_fails_fast_when_jwks_is_unreachable(self) -> None:
        def unreachable_fetch(_url: str) -> dict[str, Any]:
            raise access_module.AccessJwksError("network unreachable")

        with self.assertRaises(access_module.AccessJwksError):
            create_validator(fetch=unreachable_fetch)

    def test_validator_fails_fast_when_jwks_has_no_keys(self) -> None:
        with self.assertRaises(access_module.AccessJwksError):
            create_validator(jwks_document={"keys": []})


class ValidatorAssertionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = create_validator(jwks_document=LEGIT_JWKS)

    def verify(self, token: str) -> None:
        self.validator.verify_assertion(token)

    def test_valid_assertion_returns_claims(self) -> None:
        claims = self.validator.verify_assertion(issue_token(LEGIT_KEY))
        self.assertEqual(claims["aud"], APPLICATION_AUD)
        self.assertEqual(claims["iss"], TEAM_URL)

    def test_wrong_signature_is_rejected(self) -> None:
        token = issue_token(ATTACKER_KEY)  # kid matches JWKS, key does not
        with self.assertRaises(access_module.AccessAssertionError):
            self.verify(token)

    def test_wrong_audience_is_rejected(self) -> None:
        token = issue_token(LEGIT_KEY, audience="some-other-application-aud")
        with self.assertRaises(access_module.AccessAssertionError):
            self.verify(token)

    def test_expired_token_is_rejected(self) -> None:
        token = issue_token(LEGIT_KEY, expires_in=-600)
        with self.assertRaises(access_module.AccessAssertionError):
            self.verify(token)

    def test_not_yet_valid_token_is_rejected(self) -> None:
        token = issue_token(LEGIT_KEY, not_before=int(time.time()) + 600)
        with self.assertRaises(access_module.AccessAssertionError):
            self.verify(token)

    def test_issuer_mismatch_is_rejected(self) -> None:
        token = issue_token(
            LEGIT_KEY, issuer="https://another-team.cloudflareaccess.com"
        )
        with self.assertRaises(access_module.AccessAssertionError):
            self.verify(token)

    def test_unknown_key_id_is_rejected(self) -> None:
        token = issue_token(LEGIT_KEY, kid=ROTATED_KID)
        with self.assertRaises(access_module.AccessAssertionError):
            self.verify(token)

    def test_missing_required_claims_are_rejected(self) -> None:
        token = issue_token(LEGIT_KEY, without_claims=("sub",))
        with self.assertRaises(access_module.AccessAssertionError):
            self.verify(token)

    def test_non_rsa_algorithm_is_rejected(self) -> None:
        token = issue_token("attacker-hmac-secret", algorithm="HS256")
        with self.assertRaises(access_module.AccessAssertionError):
            self.verify(token)

    def test_garbage_token_is_rejected(self) -> None:
        with self.assertRaises(access_module.AccessAssertionError):
            self.verify("not-a-jwt")

    def test_key_rotation_is_picked_up_by_rate_limited_refresh(self) -> None:
        fetcher = RecordingFetcher()
        fetcher.push({"keys": [build_jwk(LEGIT_KEY, LEGIT_KID)]})
        fetcher.push({"keys": [build_jwk(ROTATED_KEY, ROTATED_KID)]})
        validator = create_validator(fetch=fetcher, min_refresh_interval=0.0)

        claims = validator.verify_assertion(issue_token(ROTATED_KEY, kid=ROTATED_KID))
        self.assertEqual(claims["aud"], APPLICATION_AUD)
        self.assertEqual(fetcher.calls, 2)  # initial load + rotation refresh


class PublicModeHttpTests(unittest.TestCase):
    """End-to-end public mode behaviour through the ASGI middleware."""

    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / "rates.sqlite"
        self.repository = RatesRepository(self.database_path)
        self.validator = create_validator(jwks_document=LEGIT_JWKS)
        self.client = create_public_client(self.validator, repository=self.repository)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        self.public_headers = {"host": PUBLIC_HOST, **ACCEPT_SSE}

    def post_mcp(self, headers: dict[str, str], json_body: dict[str, Any] | None = None):
        return self.client.post(
            "/mcp",
            json=json_body if json_body is not None else {"jsonrpc": "2.0", "id": 1},
            headers=headers,
        )

    def test_public_request_without_assertion_is_rejected(self) -> None:
        response = self.post_mcp(self.public_headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"error": "unauthorized"})

    def test_wrong_signature_assertion_is_rejected(self) -> None:
        response = self.post_mcp(
            {
                **self.public_headers,
                access_module.ASSERTION_HEADER: issue_token(ATTACKER_KEY),
            }
        )
        self.assertEqual(response.status_code, 401)

    def test_wrong_audience_assertion_is_rejected(self) -> None:
        response = self.post_mcp(
            {
                **self.public_headers,
                access_module.ASSERTION_HEADER: issue_token(
                    LEGIT_KEY, audience="another-aud"
                ),
            }
        )
        self.assertEqual(response.status_code, 401)

    def test_expired_assertion_is_rejected(self) -> None:
        response = self.post_mcp(
            {
                **self.public_headers,
                access_module.ASSERTION_HEADER: issue_token(
                    LEGIT_KEY, expires_in=-600
                ),
            }
        )
        self.assertEqual(response.status_code, 401)

    def test_valid_assertion_allows_authenticated_mcp_tool_call(self) -> None:
        headers = {
            **self.public_headers,
            access_module.ASSERTION_HEADER: issue_token(LEGIT_KEY),
        }
        initialize_streamable_http(self.client, headers)
        response = self.client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "save_exchange_rates",
                    "arguments": {"rates": [VALID_RATE]},
                },
            },
            headers=headers,
        )
        self.assertEqual(response.status_code, 200)
        result = parse_sse_message(response.text)
        self.assertFalse(result["result"]["isError"])
        self.assertEqual(
            result["result"]["structuredContent"],
            {"received": 1, "inserted": 1, "updated": 0, "unchanged": 0},
        )
        with closing(sqlite3.connect(self.database_path)) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM exchange_rates"
            ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_valid_assertion_also_authenticates_loopback_mcp_requests(self) -> None:
        headers = {
            "host": "127.0.0.1:8765",
            **ACCEPT_SSE,
            access_module.ASSERTION_HEADER: issue_token(LEGIT_KEY),
        }
        response = self.post_mcp(headers)
        self.assertNotIn(response.status_code, {401, 403, 421})

    def test_loopback_mcp_request_without_assertion_is_rejected(self) -> None:
        response = self.post_mcp({"host": "127.0.0.1:8765", **ACCEPT_SSE})
        self.assertEqual(response.status_code, 401)

    def test_loopback_health_check_stays_open_for_the_deploy_workflow(self) -> None:
        response = self.client.get("/health", headers={"host": "127.0.0.1:8765"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_public_health_request_without_assertion_is_rejected(self) -> None:
        response = self.client.get("/health", headers={"host": PUBLIC_HOST})
        self.assertEqual(response.status_code, 401)

    def test_host_allowlist_still_applies_after_valid_authentication(self) -> None:
        response = self.post_mcp(
            {
                "host": "attacker.example",
                **ACCEPT_SSE,
                access_module.ASSERTION_HEADER: issue_token(LEGIT_KEY),
            }
        )
        self.assertEqual(response.status_code, 421)


class PublicModeServerFactoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = create_validator(jwks_document=LEGIT_JWKS)

    def test_access_validator_instructions_replace_the_loopback_notice(self) -> None:
        server = server_module.create_server(
            public=True, access_validator=self.validator
        )
        self.assertIn("Cloudflare Access", server.instructions)
        self.assertIn("Cf-Access-Jwt-Assertion", server.instructions)

    def test_access_validator_is_rejected_in_loopback_mode(self) -> None:
        with self.assertRaises(ValueError):
            server_module.create_server(access_validator=self.validator)

    def test_access_validator_cannot_be_combined_with_oauth_configuration(self) -> None:
        authorization = server_module.AuthorizationConfiguration(
            settings=AuthSettings(
                issuer_url="https://auth.example.com",
                resource_server_url="https://mcp.franchina.qzz.io/mcp",
                required_scopes=["rates:write"],
            ),
            token_verifier=StaticTokenVerifier(),
        )
        with self.assertRaises(ValueError):
            server_module.create_server(
                authorization=authorization,
                access_validator=self.validator,
                public=True,
            )


class LoopbackModeParityTests(unittest.TestCase):
    def test_loopback_app_through_the_shared_factory_keeps_current_behaviour(
        self,
    ) -> None:
        server = server_module.create_server()
        app = server_module.create_streamable_http_app(server, stateless_http=True)
        with TestClient(app, base_url="http://127.0.0.1:8765") as client:
            self.assertEqual(client.get("/health").status_code, 200)
            self.assertEqual(
                client.post(
                    "/mcp",
                    json={},
                    headers={"host": "attacker.example"},
                ).status_code,
                421,
            )
            response = client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "id": 1},
                headers={"host": "localhost:8765", **ACCEPT_SSE},
            )
            self.assertNotIn(response.status_code, {401, 403, 421})


class StaticTokenVerifier:
    async def verify_token(self, token: str) -> None:
        return None


if __name__ == "__main__":
    unittest.main()
