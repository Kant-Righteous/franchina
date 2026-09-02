import http.client
import io
import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from scripts import purge_cloudflare


class PurgeCloudflareTests(unittest.TestCase):
    def setUp(self):
        self.token = "test-only-cloudflare-token"
        self.zone_id = "0123456789abcdef0123456789abcdef"
        self.environment = patch.dict(
            os.environ,
            {
                "CLOUDFLARE_ZONE_ID": self.zone_id,
                "CLOUDFLARE_API_TOKEN": self.token,
            },
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.transport = patch.object(purge_cloudflare.http.client, "HTTPSConnection")
        self.connection_type = self.transport.start()
        self.addCleanup(self.transport.stop)
        self.connection = self.connection_type.return_value
        self.response = self.connection.getresponse.return_value
        self.response.status = 200
        self.response.read.return_value = (
            b'{"success":true,"errors":[],"messages":[],"result":{"id":"test-purge"}}'
        )

    def run_client(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = purge_cloudflare.main()
        output = stdout.getvalue() + stderr.getvalue()
        self.assertNotIn(self.token, output)
        self.assertNotIn("Authorization", output)
        return result, output

    def test_success_sends_authenticated_purge_everything_to_official_api(self):
        result, _ = self.run_client()
        self.assertEqual(result, 0)
        self.connection_type.assert_called_once_with("api.cloudflare.com", timeout=30)
        args, kwargs = self.connection.request.call_args
        self.assertEqual(
            args,
            ("POST", "/client/v4/zones/0123456789abcdef0123456789abcdef/purge_cache"),
        )
        self.assertEqual(json.loads(kwargs["body"]), {"purge_everything": True})
        self.assertEqual(
            kwargs["headers"]["Authorization"], "Bearer test-only-cloudflare-token"
        )
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")
        self.connection.close.assert_called_once()

    def test_http_errors_and_redirects_fail_without_printing_response(self):
        for status in (301, 302, 307, 400, 401, 429, 500):
            with self.subTest(status=status):
                self.response.status = status
                self.response.read.return_value = self.token.encode()
                result, output = self.run_client()
                self.assertEqual(result, 1)
                self.assertIn(str(status), output)

    def test_api_failure_or_missing_boolean_success_fails(self):
        for payload in (
            {"success": False, "errors": [{"message": "test-only-cloudflare-token"}]},
            {"success": "true"},
            {"success": 1},
            {},
            [],
            None,
        ):
            with self.subTest(payload=payload):
                self.response.read.return_value = json.dumps(payload).encode()
                self.assertEqual(self.run_client()[0], 1)

    def test_invalid_json_fails_without_printing_response(self):
        for body in (b"", b"not-json", b"\xff", self.token.encode()):
            with self.subTest(body=body):
                self.response.read.return_value = body
                self.assertEqual(self.run_client()[0], 1)

    def test_network_errors_fail_without_printing_exception_details(self):
        for error in (
            OSError(self.token),
            TimeoutError(self.token),
            http.client.HTTPException(self.token),
        ):
            with self.subTest(error=type(error).__name__):
                self.connection.request.side_effect = error
                self.assertEqual(self.run_client()[0], 1)
        self.assertEqual(self.connection.close.call_count, 3)

    def test_invalid_configuration_fails_before_connecting(self):
        for name, value in (
            ("CLOUDFLARE_ZONE_ID", ""),
            ("CLOUDFLARE_ZONE_ID", "../other-zone"),
            ("CLOUDFLARE_API_TOKEN", ""),
            ("CLOUDFLARE_API_TOKEN", "unsafe\r\nheader"),
        ):
            with (
                self.subTest(name=name, value=value),
                patch.dict(os.environ, {name: value}),
            ):
                self.assertEqual(self.run_client()[0], 1)
        self.connection_type.assert_not_called()


if __name__ == "__main__":
    unittest.main()
