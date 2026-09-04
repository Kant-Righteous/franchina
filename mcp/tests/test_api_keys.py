from __future__ import annotations

import io
import os
import sqlite3
import unittest
from contextlib import closing, redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from starlette.testclient import TestClient
from test_cloudflare_access import (
    ACCEPT_SSE,
    VALID_RATE,
    initialize_streamable_http,
    parse_sse_message,
)

from franchina_mcp import config as config_module
from franchina_mcp import keys as keys_module
from franchina_mcp import server as server_module
from franchina_mcp.api_keys import (
    ApiKeyAuthenticator,
    ApiKeyError,
    ApiKeyRepository,
    hash_secret,
    parse_api_key,
)

PUBLIC_HOST = "mcp.franchina.qzz.io"
LOOPBACK_HOST = "127.0.0.1:8765"
MCP_ROOT = Path(__file__).resolve().parents[1]


class ModeResolutionTests(unittest.TestCase):
    def test_unset_or_loopback_defaults_to_loopback(self) -> None:
        for environment in (
            {},
            {config_module.MODE_ENV: ""},
            {config_module.MODE_ENV: " loopback "},
        ):
            with self.subTest(environment=environment):
                self.assertEqual(
                    config_module.resolve_run_mode(environment),
                    config_module.LOOPBACK_MODE,
                )

    def test_public_modes_are_explicit(self) -> None:
        for mode in (
            config_module.CLOUDFLARE_ACCESS_MODE,
            config_module.API_KEY_MODE,
        ):
            self.assertEqual(
                config_module.resolve_run_mode({config_module.MODE_ENV: mode}), mode
            )

    def test_unknown_mode_fails_startup(self) -> None:
        with self.assertRaises(SystemExit):
            config_module.resolve_run_mode({config_module.MODE_ENV: "public"})


class AuthDatabasePathTests(unittest.TestCase):
    def test_auth_database_defaults_to_a_file_separate_from_rates(self) -> None:
        auth_path = config_module.resolve_auth_database_path()
        rates_path = config_module.resolve_database_path()
        self.assertEqual(auth_path.name, "dev_auth.sqlite")
        self.assertNotEqual(auth_path, rates_path)

    def test_auth_database_path_env_override(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            configured = str(Path(temporary_directory) / "custom-auth.sqlite")
            with patch.dict(
                os.environ,
                {config_module.AUTH_DATABASE_PATH_ENV: configured},
            ):
                self.assertEqual(
                    config_module.resolve_auth_database_path(),
                    Path(configured),
                )

    def test_auth_database_path_env_must_not_be_empty(self) -> None:
        with patch.dict(
            os.environ, {config_module.AUTH_DATABASE_PATH_ENV: "   "}
        ), self.assertRaises(ValueError):
            config_module.resolve_auth_database_path()


class ApiKeyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.auth_path = Path(self.temporary_directory.name) / "auth.sqlite"
        self.rates_path = Path(self.temporary_directory.name) / "rates.sqlite"
        self.repository = ApiKeyRepository(self.auth_path)
        self.rates_repository = server_module.RatesRepository(self.rates_path)

    def create_key(self, *, name: str = "Zhengyi", scopes: tuple[str, ...] = ("rates:write",)) -> str:
        _record, plaintext_key = self.repository.create(name=name, scopes=scopes)
        return plaintext_key

    def create_client(
        self, *, max_request_body_bytes: int | None = None
    ) -> TestClient:
        authenticator = ApiKeyAuthenticator(self.repository)
        server = server_module.create_server(
            self.rates_repository, public=True, api_key_authenticator=authenticator
        )
        app = server_module.create_streamable_http_app(
            server,
            api_key_authenticator=authenticator,
            public=True,
            stateless_http=True,
            max_request_body_bytes=max_request_body_bytes,
        )
        return TestClient(app, base_url="http://127.0.0.1:8765")

    def set_raw_expiry(self, key_id: str, value: str | None) -> None:
        with closing(sqlite3.connect(self.auth_path)) as connection:
            connection.execute(
                "UPDATE api_keys SET expires_at = ? WHERE key_id = ?",
                (value, key_id),
            )
            connection.commit()

    def key_id_of(self, plaintext_key: str) -> str:
        key_id, _secret = parse_api_key(plaintext_key)
        return key_id

    def rates_row_count(self) -> int:
        with closing(sqlite3.connect(self.rates_path)) as connection:
            return connection.execute(
                "SELECT COUNT(*) FROM exchange_rates"
            ).fetchone()[0]

    def table_names(self, database_path: Path) -> set[str]:
        with closing(sqlite3.connect(database_path)) as connection:
            return {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }


class KeyMaterialTests(ApiKeyTestCase):
    def test_created_key_has_expected_shape_and_is_shown_once(self) -> None:
        record, plaintext_key = self.repository.create(
            name="Zhengyi", scopes=("rates:write",)
        )

        prefix, key_id, secret = plaintext_key.split("_", 2)
        self.assertEqual(prefix, "fmcp")
        self.assertEqual(key_id, record.key_id)
        self.assertEqual(len(key_id), 16)
        self.assertEqual(len(secret), 64)
        int(key_id, 16)  # hex
        int(secret, 16)  # hex: 256-bit CSPRNG secret

    def test_database_never_stores_the_plaintext_key(self) -> None:
        record, plaintext_key = self.repository.create(
            name="Zhengyi", scopes=("rates:write",)
        )
        _prefix, _key_id, secret = plaintext_key.split("_", 2)

        with closing(sqlite3.connect(self.auth_path)) as connection:
            rows = connection.execute(
                "SELECT key_id, name, key_hash, scopes FROM api_keys"
            ).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertNotEqual(rows[0][2], secret)
        self.assertNotIn(plaintext_key, rows[0])
        self.assertEqual(rows[0][2], hash_secret(secret))
        self.assertEqual(rows[0][2], record.key_hash)

        raw_file = self.auth_path.read_bytes()
        self.assertNotIn(secret.encode("ascii"), raw_file)
        self.assertNotIn(plaintext_key.encode("ascii"), raw_file)

    def test_parse_api_key_rejects_malformed_values(self) -> None:
        for presented in ("", "fmcp_", "fmcp_only", "nope_a_b", "fmcp_a_", "fmcp__b"):
            with (
                self.subTest(presented=presented),
                self.assertRaises(ApiKeyError),
            ):
                parse_api_key(presented)


class RepositoryTests(ApiKeyTestCase):
    def test_create_find_and_list_roundtrip(self) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        record, _plaintext_key = self.repository.create(
            name="Zhengyi", scopes=("b", "rates:write", "a"), expires_at=expires_at
        )

        found = self.repository.find(record.key_id)
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "Zhengyi")
        self.assertEqual(found.scopes, frozenset({"rates:write", "a", "b"}))
        self.assertTrue(found.enabled)
        self.assertIsNotNone(found.created_at)
        self.assertIsNotNone(found.expires_at)
        self.assertTrue(found.expires_at.endswith("Z"))
        self.assertIsNone(found.last_used_at)

        listed = self.repository.list_keys()
        self.assertEqual([item.key_id for item in listed], [record.key_id])

    def test_find_returns_none_for_unknown_key_id(self) -> None:
        self.assertIsNone(self.repository.find("0" * 16))

    def test_set_enabled_and_revoke(self) -> None:
        plaintext_key = self.create_key()

        self.assertTrue(self.repository.revoke(self.key_id_of(plaintext_key)))
        self.assertFalse(self.repository.find(self.key_id_of(plaintext_key)).enabled)

        self.assertTrue(
            self.repository.set_enabled(self.key_id_of(plaintext_key), True)
        )
        self.assertTrue(self.repository.find(self.key_id_of(plaintext_key)).enabled)

        self.assertFalse(self.repository.set_enabled("0" * 16, False))

    def test_touch_updates_last_used_at(self) -> None:
        plaintext_key = self.create_key()
        key_id = self.key_id_of(plaintext_key)

        self.assertIsNone(self.repository.find(key_id).last_used_at)
        self.repository.touch(key_id)
        self.assertIsNotNone(self.repository.find(key_id).last_used_at)

    def test_reopening_the_database_keeps_existing_keys(self) -> None:
        plaintext_key = self.create_key()

        reopened = ApiKeyRepository(self.auth_path)
        found = reopened.find(self.key_id_of(plaintext_key))

        self.assertIsNotNone(found)
        self.assertTrue(found.enabled)

    def test_create_rejects_naive_expiry_and_empty_name(self) -> None:
        with self.assertRaises(ValueError):
            self.repository.create(
                name="Zhengyi",
                expires_at=datetime.now() + timedelta(days=1),  # noqa: DTZ005 - naive on purpose
            )
        with self.assertRaises(ValueError):
            self.repository.create(name="   ")


class AuthenticatorTests(ApiKeyTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.authenticator = ApiKeyAuthenticator(self.repository)

    def test_valid_key_authenticates(self) -> None:
        plaintext_key = self.create_key()
        record = self.authenticator.authenticate(plaintext_key)
        self.assertEqual(record.scopes, frozenset({"rates:write"}))

    def test_wrong_secret_is_rejected(self) -> None:
        plaintext_key = self.create_key()
        key_id, _secret = parse_api_key(plaintext_key)
        forged = f"fmcp_{key_id}_{'0' * 64}"
        with self.assertRaises(ApiKeyError):
            self.authenticator.authenticate(forged)

    def test_unknown_key_is_rejected(self) -> None:
        with self.assertRaises(ApiKeyError):
            self.authenticator.authenticate(f"fmcp_{'0' * 16}_{'1' * 64}")

    def test_disabled_key_is_rejected(self) -> None:
        plaintext_key = self.create_key()
        self.repository.revoke(self.key_id_of(plaintext_key))
        with self.assertRaises(ApiKeyError):
            self.authenticator.authenticate(plaintext_key)

    def test_expired_key_is_rejected(self) -> None:
        plaintext_key = self.create_key()
        self.set_raw_expiry(
            self.key_id_of(plaintext_key),
            "2000-01-01T00:00:00Z",
        )
        with self.assertRaises(ApiKeyError):
            self.authenticator.authenticate(plaintext_key)

    def test_future_expiry_is_accepted(self) -> None:
        plaintext_key = self.create_key()
        self.set_raw_expiry(
            self.key_id_of(plaintext_key),
            (datetime.now(timezone.utc) + timedelta(days=1))
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z"),
        )
        record = self.authenticator.authenticate(plaintext_key)
        self.assertTrue(record.enabled)

    def test_unparseable_expiry_fails_closed(self) -> None:
        plaintext_key = self.create_key()
        self.set_raw_expiry(self.key_id_of(plaintext_key), "not-a-timestamp")
        with self.assertRaises(ApiKeyError):
            self.authenticator.authenticate(plaintext_key)


class ApiKeyHttpTests(ApiKeyTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = self.create_client()
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        self.public_headers = {"host": PUBLIC_HOST, **ACCEPT_SSE}

    def post_mcp(
        self,
        headers: dict[str, str],
        json_body: object | None = None,
    ):
        return self.client.post(
            "/mcp",
            json=json_body if json_body is not None else {"jsonrpc": "2.0", "id": 1},
            headers=headers,
        )

    def bearer(self, key: str | None) -> dict[str, str]:
        if key is None:
            return {}
        return {"authorization": f"Bearer {key}"}

    def test_missing_authorization_header_is_rejected(self) -> None:
        response = self.post_mcp(self.public_headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"error": "unauthorized"})

    def test_non_bearer_schemes_are_rejected(self) -> None:
        for scheme in ("Basic dXNlcjpwYXNz", "Token abc", "Bearer"):
            with self.subTest(scheme=scheme):
                response = self.post_mcp(
                    {**self.public_headers, "authorization": scheme}
                )
                self.assertEqual(response.status_code, 401)

    def test_malformed_keys_are_rejected(self) -> None:
        for key in ("not-a-key", "fmcp_", "fmcp_onlyid", "fmcp_abc_"):
            with self.subTest(key=key):
                response = self.post_mcp(
                    {**self.public_headers, **self.bearer(key)}
                )
                self.assertEqual(response.status_code, 401)

    def test_unknown_key_is_rejected_over_http(self) -> None:
        response = self.post_mcp(
            {**self.public_headers, **self.bearer(f"fmcp_{'0' * 16}_{'1' * 64}")}
        )
        self.assertEqual(response.status_code, 401)

    def test_wrong_secret_is_rejected_over_http(self) -> None:
        plaintext_key = self.create_key()
        key_id, _secret = parse_api_key(plaintext_key)
        response = self.post_mcp(
            {**self.public_headers, **self.bearer(f"fmcp_{key_id}_{'0' * 64}")}
        )
        self.assertEqual(response.status_code, 401)

    def test_disabled_key_is_rejected_over_http(self) -> None:
        plaintext_key = self.create_key()
        self.repository.revoke(self.key_id_of(plaintext_key))
        response = self.post_mcp(
            {**self.public_headers, **self.bearer(plaintext_key)}
        )
        self.assertEqual(response.status_code, 401)

    def test_expired_key_is_rejected_over_http(self) -> None:
        plaintext_key = self.create_key()
        self.set_raw_expiry(self.key_id_of(plaintext_key), "2000-01-01T00:00:00Z")
        response = self.post_mcp(
            {**self.public_headers, **self.bearer(plaintext_key)}
        )
        self.assertEqual(response.status_code, 401)

    def test_valid_key_can_call_save_exchange_rates(self) -> None:
        plaintext_key = self.create_key()
        headers = {
            **self.public_headers,
            **self.bearer(plaintext_key),
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
        self.assertEqual(self.rates_row_count(), 1)

        # The two databases stay fully separate.
        self.assertEqual(
            self.table_names(self.auth_path), {"api_keys"}
        )
        self.assertEqual(
            self.table_names(self.rates_path), {"exchange_rates"}
        )

    def test_keys_of_different_users_authenticate_independently(self) -> None:
        for name in ("Zhengyi", "Alice"):
            plaintext_key = self.create_key(name=name)
            response = self.post_mcp(
                {**self.public_headers, **self.bearer(plaintext_key)}
            )
            self.assertNotEqual(response.status_code, 401, name)

    def test_revoked_key_fails_while_other_keys_keep_working(self) -> None:
        key_a = self.create_key(name="Zhengyi")
        key_b = self.create_key(name="Alice")
        headers_b = {**self.public_headers, **self.bearer(key_b)}

        self.repository.revoke(self.key_id_of(key_a))
        revoked_response = self.post_mcp({**self.public_headers, **self.bearer(key_a)})
        self.assertEqual(revoked_response.status_code, 401)

        initialize_streamable_http(self.client, headers_b)
        active_response = self.post_mcp(headers_b)
        self.assertNotEqual(active_response.status_code, 401)

    def test_key_without_scope_can_initialize_but_not_write(self) -> None:
        plaintext_key = self.create_key(scopes=())
        headers = {**self.public_headers, **self.bearer(plaintext_key)}

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
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"error": "insufficient_scope"})
        self.assertEqual(self.rates_row_count(), 0)

    def test_scope_is_enforced_inside_batched_requests(self) -> None:
        plaintext_key = self.create_key(scopes=())
        response = self.post_mcp(
            {**self.public_headers, **self.bearer(plaintext_key)},
            json_body=[
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {
                    "jsonrpc": "2.0",
                    "id": 5,
                    "method": "tools/call",
                    "params": {
                        "name": "save_exchange_rates",
                        "arguments": {"rates": [VALID_RATE]},
                    },
                },
            ],
        )
        self.assertEqual(response.status_code, 403)

    def test_loopback_health_stays_open_for_the_deploy_workflow(self) -> None:
        response = self.client.get("/health", headers={"host": LOOPBACK_HOST})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_public_health_is_not_openly_accessible(self) -> None:
        anonymous = self.client.get("/health", headers={"host": PUBLIC_HOST})
        self.assertEqual(anonymous.status_code, 401)

        plaintext_key = self.create_key()
        authenticated = self.client.get(
            "/health",
            headers={"host": PUBLIC_HOST, **self.bearer(plaintext_key)},
        )
        self.assertEqual(authenticated.status_code, 200)

    def test_loopback_mcp_still_requires_a_key(self) -> None:
        anonymous = self.post_mcp({"host": LOOPBACK_HOST, **ACCEPT_SSE})
        self.assertEqual(anonymous.status_code, 401)

        plaintext_key = self.create_key()
        authenticated = self.post_mcp(
            {
                "host": LOOPBACK_HOST,
                **ACCEPT_SSE,
                **self.bearer(plaintext_key),
            }
        )
        self.assertNotIn(authenticated.status_code, {401, 403, 421})

    def test_host_allowlist_still_applies_after_authentication(self) -> None:
        plaintext_key = self.create_key()
        response = self.post_mcp(
            {
                "host": "attacker.example",
                **ACCEPT_SSE,
                **self.bearer(plaintext_key),
            }
        )
        self.assertEqual(response.status_code, 421)

    def test_last_used_at_updates_after_successful_request(self) -> None:
        plaintext_key = self.create_key()
        key_id = self.key_id_of(plaintext_key)
        self.assertIsNone(self.repository.find(key_id).last_used_at)

        self.post_mcp({**self.public_headers, **self.bearer(plaintext_key)})
        self.assertIsNotNone(self.repository.find(key_id).last_used_at)

    def test_oversized_request_body_is_rejected(self) -> None:
        client = self.create_client(max_request_body_bytes=8)
        with client:
            plaintext_key = self.create_key()
            response = client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "id": 1, "method": "initialize",
                      "params": {"protocolVersion": "2025-06-18",
                                 "capabilities": {},
                                 "clientInfo": {"name": "t", "version": "0"}}},
                headers={
                    "host": PUBLIC_HOST,
                    **ACCEPT_SSE,
                    **self.bearer(plaintext_key),
                },
            )
        self.assertEqual(response.status_code, 413)

    def test_key_and_authorization_header_never_appear_in_logs(self) -> None:
        key_a = self.create_key()
        self.repository.revoke(self.key_id_of(key_a))

        with self.assertLogs(level="WARNING") as captured:
            response = self.post_mcp({**self.public_headers, **self.bearer(key_a)})
        self.assertEqual(response.status_code, 401)
        logged = "\n".join(captured.output)
        self.assertNotIn(key_a, logged)
        self.assertNotIn(key_a.split("_", 2)[2], logged)


class ServerFactoryTests(ApiKeyTestCase):
    def test_api_key_authenticator_instructions_replace_the_loopback_notice(self) -> None:
        authenticator = ApiKeyAuthenticator(self.repository)
        server = server_module.create_server(
            public=True, api_key_authenticator=authenticator
        )
        self.assertIn("API key", server.instructions)

    def test_api_key_authenticator_is_rejected_in_loopback_mode(self) -> None:
        authenticator = ApiKeyAuthenticator(self.repository)
        with self.assertRaises(ValueError):
            server_module.create_server(api_key_authenticator=authenticator)

    def test_api_key_authenticator_cannot_be_combined_with_other_backends(self) -> None:
        authenticator = ApiKeyAuthenticator(self.repository)
        access_validator = self.create_cloudflare_validator()
        with self.assertRaises(ValueError):
            server_module.create_server(
                public=True,
                access_validator=access_validator,
                api_key_authenticator=authenticator,
            )

    def create_cloudflare_validator(self):
        from test_cloudflare_access import create_validator

        return create_validator()


class LoopbackModeUnchangedTests(ApiKeyTestCase):
    def test_loopback_app_needs_no_authentication(self) -> None:
        server = server_module.create_server(self.rates_repository)
        app = server_module.create_streamable_http_app(
            server, stateless_http=True
        )
        with TestClient(app, base_url="http://127.0.0.1:8765") as client:
            self.assertEqual(client.get("/health").status_code, 200)
            response = client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "id": 1},
                headers={"host": LOOPBACK_HOST, **ACCEPT_SSE},
            )
            self.assertNotIn(response.status_code, {401, 403, 421})


class KeysCliTests(ApiKeyTestCase):
    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            patch.dict(
                os.environ,
                {config_module.AUTH_DATABASE_PATH_ENV: str(self.auth_path)},
            ),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            exit_code = keys_module.main(list(argv))
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def created_key_from_output(self, output: str) -> str:
        for line in output.splitlines():
            if line.startswith("fmcp_"):
                return line.strip()
        raise AssertionError(f"no key printed in CLI output: {output!r}")

    def test_create_prints_the_plaintext_key_exactly_once(self) -> None:
        exit_code, stdout, _stderr = self.run_cli(
            "create", "--name", "Zhengyi", "--scope", "rates:write"
        )
        self.assertEqual(exit_code, 0)
        plaintext_key = self.created_key_from_output(stdout)
        self.assertEqual(stdout.count(plaintext_key), 1)
        self.assertIn("shown only once", stdout)

        record = self.repository.find(self.key_id_of(plaintext_key))
        self.assertIsNotNone(record)
        self.assertEqual(record.name, "Zhengyi")
        self.assertEqual(record.scopes, frozenset({"rates:write"}))

    def test_created_key_authenticates_over_http(self) -> None:
        _code, stdout, _stderr = self.run_cli(
            "create", "--name", "Zhengyi", "--scope", "rates:write"
        )
        plaintext_key = self.created_key_from_output(stdout)
        with self.create_client() as client:
            response = client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "id": 1},
                headers={
                    "host": PUBLIC_HOST,
                    **ACCEPT_SSE,
                    "authorization": f"Bearer {plaintext_key}",
                },
            )
        self.assertNotEqual(response.status_code, 401)

    def test_create_accepts_repeated_scopes_and_expiry(self) -> None:
        _code, stdout, _stderr = self.run_cli(
            "create",
            "--name", "Bot",
            "--scope", "rates:write",
            "--scope", "extra",
            "--expires-in-days", "7",
        )
        plaintext_key = self.created_key_from_output(stdout)
        record = self.repository.find(self.key_id_of(plaintext_key))
        self.assertEqual(record.scopes, frozenset({"rates:write", "extra"}))
        self.assertIsNotNone(record.expires_at)

    def test_list_shows_metadata_but_never_the_secret(self) -> None:
        _code, create_output, _stderr = self.run_cli(
            "create", "--name", "Zhengyi", "--scope", "rates:write"
        )
        plaintext_key = self.created_key_from_output(create_output)
        secret = plaintext_key.split("_", 2)[2]

        exit_code, stdout, _stderr = self.run_cli("list")
        self.assertEqual(exit_code, 0)
        self.assertIn("Zhengyi", stdout)
        self.assertIn(self.key_id_of(plaintext_key), stdout)
        self.assertNotIn(secret, stdout)
        self.assertNotIn(plaintext_key, stdout)

    def test_revoke_disables_the_key(self) -> None:
        _code, create_output, _stderr = self.run_cli(
            "create", "--name", "Zhengyi", "--scope", "rates:write"
        )
        plaintext_key = self.created_key_from_output(create_output)
        key_id = self.key_id_of(plaintext_key)

        exit_code, stdout, _stderr = self.run_cli("revoke", key_id)
        self.assertEqual(exit_code, 0)
        self.assertIn(key_id, stdout)

        with self.create_client() as client:
            response = client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "id": 1},
                headers={
                    "host": PUBLIC_HOST,
                    **ACCEPT_SSE,
                    "authorization": f"Bearer {plaintext_key}",
                },
            )
        self.assertEqual(response.status_code, 401)

        _code, list_output, _stderr = self.run_cli("list")
        self.assertIn("revoked", list_output)

    def test_revoke_unknown_key_fails(self) -> None:
        exit_code, _stdout, stderr = self.run_cli("revoke", "0" * 16)
        self.assertEqual(exit_code, 1)
        self.assertIn("0" * 16, stderr)

    def test_disable_and_enable_round_trip(self) -> None:
        _code, create_output, _stderr = self.run_cli(
            "create", "--name", "Zhengyi", "--scope", "rates:write"
        )
        plaintext_key = self.created_key_from_output(create_output)
        key_id = self.key_id_of(plaintext_key)
        request_headers = {
            "host": PUBLIC_HOST,
            **ACCEPT_SSE,
            "authorization": f"Bearer {plaintext_key}",
        }

        self.assertEqual(self.run_cli("disable", key_id)[0], 0)
        with self.create_client() as client:
            self.assertEqual(
                client.post("/mcp", json={"jsonrpc": "2.0", "id": 1},
                            headers=request_headers).status_code,
                401,
            )

        self.assertEqual(self.run_cli("enable", key_id)[0], 0)
        with self.create_client() as client:
            self.assertNotEqual(
                client.post("/mcp", json={"jsonrpc": "2.0", "id": 1},
                            headers=request_headers).status_code,
                401,
            )


class DeploymentIsolationTests(unittest.TestCase):
    def test_gitignore_excludes_sqlite_files(self) -> None:
        gitignore = (MCP_ROOT.parent / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("*.sqlite", gitignore)

    def test_release_archive_excludes_sqlite_and_workflow_never_touches_auth(self) -> None:
        workflow = (
            MCP_ROOT.parent / ".github" / "workflows" / "deploy_mcp.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("--exclude='*.sqlite'", workflow)
        self.assertNotIn("auth.sqlite", workflow)
        self.assertNotIn("api_keys", workflow)
        self.assertNotIn("franchina_mcp.keys", workflow)


if __name__ == "__main__":
    unittest.main()
