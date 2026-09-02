from __future__ import annotations

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from starlette.testclient import TestClient

from franchina_mcp import server as server_module


class TestTokenVerifier:
    async def verify_token(self, token: str) -> AccessToken | None:
        if token != "valid-test-token":
            return None
        return AccessToken(
            token=token,
            client_id="test-client",
            scopes=["rates:write"],
            resource="https://mcp.franchina.qzz.io/mcp",
        )


def create_authorization() -> server_module.AuthorizationConfiguration:
    return server_module.AuthorizationConfiguration(
        settings=AuthSettings(
            issuer_url="https://auth.example.com",
            resource_server_url="https://mcp.franchina.qzz.io/mcp",
            required_scopes=["rates:write"],
        ),
        token_verifier=TestTokenVerifier(),
    )


def create_http_client(
    *,
    authorization: server_module.AuthorizationConfiguration | None = None,
    public: bool = False,
) -> TestClient:
    server = server_module.create_server(
        authorization=authorization,
        public=public,
    )
    app = server.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        transport_security=server_module.create_transport_security_settings(
            public=public,
            authorization=authorization,
        ),
        host="127.0.0.1",
    )
    return TestClient(app, base_url="http://127.0.0.1:8765")


class HealthRouteTests(unittest.TestCase):
    def test_health_is_fixed_and_does_not_initialize_the_database(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "rates.sqlite"
            with (
                patch.dict(
                    os.environ,
                    {"FRANCHINA_MCP_DB_PATH": str(database_path)},
                    clear=False,
                ),
                create_http_client() as client,
            ):
                response = client.get("/health")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"status": "ok"})
            self.assertFalse(database_path.exists())


class TransportSecurityTests(unittest.TestCase):
    def test_rejects_unexpected_host(self) -> None:
        with create_http_client() as client:
            response = client.post(
                "/mcp",
                json={},
                headers={"host": "attacker.example"},
            )

        self.assertEqual(response.status_code, 421)

    def test_loopback_accepts_local_hosts(self) -> None:
        cases = [
            ("127.0.0.1:8765", None),
            ("localhost:8765", None),
        ]

        with create_http_client() as client:
            for host, origin in cases:
                headers = {"host": host}
                if origin is not None:
                    headers["origin"] = origin
                with self.subTest(host=host, origin=origin):
                    response = client.post("/mcp", json={}, headers=headers)
                    self.assertNotIn(response.status_code, {403, 421})

    def test_loopback_rejects_public_host(self) -> None:
        with create_http_client() as client:
            response = client.post(
                "/mcp",
                json={},
                headers={"host": "mcp.franchina.qzz.io"},
            )

        self.assertEqual(response.status_code, 421)

    def test_rejects_every_origin_except_the_expected_https_origin(self) -> None:
        with create_http_client(
            authorization=create_authorization(),
            public=True,
        ) as client:
            for origin in (
                "http://mcp.franchina.qzz.io",
                "http://localhost:3000",
                "https://attacker.example",
            ):
                with self.subTest(origin=origin):
                    response = client.post(
                        "/mcp",
                        json={},
                        headers={
                            "host": "mcp.franchina.qzz.io",
                            "origin": origin,
                            "authorization": "Bearer valid-test-token",
                        },
                    )
                    self.assertEqual(response.status_code, 403)


class AuthorizationIntegrationTests(unittest.TestCase):
    def test_public_mode_without_authorization_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            server_module.create_server(public=True)

    def test_public_mode_rejects_missing_resource_server_url(self) -> None:
        incomplete_authorization = server_module.AuthorizationConfiguration(
            settings=AuthSettings(
                issuer_url="https://auth.example.com",
                resource_server_url=None,
                required_scopes=["rates:write"],
            ),
            token_verifier=TestTokenVerifier(),
        )

        with self.assertRaises(ValueError):
            server_module.create_server(
                authorization=incomplete_authorization,
                public=True,
            )

    def test_official_authorization_configuration_rejects_anonymous_mcp(self) -> None:
        authorization = create_authorization()

        with create_http_client(
            authorization=authorization,
            public=True,
        ) as client:
            authorized_response = client.post(
                "/mcp",
                json={},
                headers={
                    "host": "mcp.franchina.qzz.io",
                    "origin": "https://mcp.franchina.qzz.io",
                    "authorization": "Bearer valid-test-token",
                },
            )
            anonymous_response = client.post(
                "/mcp",
                json={},
                headers={
                    "host": "mcp.franchina.qzz.io",
                    "origin": "https://mcp.franchina.qzz.io",
                },
            )

        self.assertNotIn(authorized_response.status_code, {403, 421})
        self.assertEqual(anonymous_response.status_code, 401)
        self.assertIn("Bearer", anonymous_response.headers["www-authenticate"])
        self.assertIn(
            "resource_metadata=", anonymous_response.headers["www-authenticate"]
        )


if __name__ == "__main__":
    unittest.main()
