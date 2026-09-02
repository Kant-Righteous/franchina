from __future__ import annotations

import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from mcp import Client

from franchina_mcp.database import RatesRepository
from franchina_mcp.server import create_server

VALID_RATE = {
    "date": "2026-09-02",
    "source": "European Central Bank",
    "currency": "EUR",
    "rate_type": "reference",
    "rate": "7.8633",
    "source_url": "https://example.com/rates",
}


class McpServerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / "rates.sqlite"
        self.repository = RatesRepository(self.database_path)
        self.server = create_server(self.repository)

    async def test_exposes_only_the_exchange_rate_write_tool(self) -> None:
        async with Client(self.server, raise_exceptions=True) as client:
            result = await client.list_tools()

        self.assertEqual([tool.name for tool in result.tools], ["save_exchange_rates"])

    async def test_tool_schema_defines_cny_per_foreign_currency_semantics(self) -> None:
        async with Client(self.server, raise_exceptions=True) as client:
            result = await client.list_tools()

        tool = result.tools[0]
        rate_schema = tool.input_schema["$defs"]["ExchangeRateInput"]
        self.assertEqual(rate_schema["properties"]["currency"]["enum"], ["EUR", "USD"])
        self.assertIn("1 currency = rate CNY", rate_schema["description"])
        self.assertIn(
            "Foreign currency priced in CNY",
            rate_schema["properties"]["currency"]["description"],
        )
        self.assertIn(
            "1 currency = rate CNY",
            rate_schema["properties"]["rate"]["description"],
        )
        self.assertIn("1 currency = rate CNY", tool.description)
        self.assertIn("divide it by 100", self.server.instructions)

    def test_unauthenticated_server_is_described_as_loopback_only(self) -> None:
        self.assertIn("not ready for a public reverse proxy", self.server.instructions)

    async def test_save_exchange_rates_writes_through_mcp(self) -> None:
        async with Client(self.server, raise_exceptions=True) as client:
            result = await client.call_tool(
                "save_exchange_rates", {"rates": [VALID_RATE]}
            )

        self.assertFalse(result.is_error)
        self.assertEqual(
            result.structured_content,
            {"received": 1, "inserted": 1, "updated": 0, "unchanged": 0},
        )
        with closing(sqlite3.connect(self.database_path)) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM exchange_rates"
            ).fetchone()[0]
        self.assertEqual(count, 1)

    async def test_rejects_arbitrary_sql_arguments(self) -> None:
        async with Client(self.server, raise_exceptions=True) as client:
            result = await client.call_tool(
                "save_exchange_rates", {"sql": "DROP TABLE exchange_rates"}
            )

        self.assertTrue(result.is_error)
        with closing(sqlite3.connect(self.database_path)) as connection:
            table_exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'exchange_rates'"
            ).fetchone()
        self.assertEqual(table_exists, (1,))

    async def test_rejects_extra_fields_inside_a_rate(self) -> None:
        invalid_rate = {**VALID_RATE, "sql": "SELECT * FROM exchange_rates"}

        async with Client(self.server, raise_exceptions=True) as client:
            result = await client.call_tool(
                "save_exchange_rates", {"rates": [invalid_rate]}
            )

        self.assertTrue(result.is_error)
        with closing(sqlite3.connect(self.database_path)) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM exchange_rates"
            ).fetchone()[0]
        self.assertEqual(count, 0)
