import io
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing, redirect_stderr
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from scripts import export_mcp_rates

SCHEMA = """
CREATE TABLE exchange_rates (
    "date" TEXT NOT NULL,
    source TEXT NOT NULL,
    currency TEXT NOT NULL,
    rate_type TEXT NOT NULL,
    rate TEXT NOT NULL,
    source_url TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY ("date", source, currency, rate_type)
) WITHOUT ROWID
"""

LATEST = "2026-09-30"
BOC_URL = "https://www.boc.cn/sourcedb/whpj/"


class ExportMcpRatesTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.db_path = Path(directory.name) / "rates.sqlite"
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(SCHEMA)
            connection.commit()

    def insert(self, *rows):
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.executemany(
                "INSERT INTO exchange_rates VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(*row, "2026-09-30T15:00:00Z") for row in rows],
            )
            connection.commit()

    def export(self):
        return export_mcp_rates.export(
            self.db_path,
            now=datetime(2026, 10, 1, 0, 0, 5, 123, tzinfo=timezone.utc),
        )

    def test_keeps_one_preferred_rate_type_per_source(self):
        self.insert(
            (LATEST, "BOC", "EUR", "spot_buy", "7.5818", BOC_URL),
            (LATEST, "BOC", "EUR", "spot_sell", "7.6373", BOC_URL),
            (LATEST, "BOC", "EUR", "reference", "7.6215", BOC_URL),
            (LATEST, "BOC", "USD", "spot_sell", "6.726", BOC_URL),
            (LATEST, "ALIPAY", "EUR", "alipay_settlement", "7.6442", "https://www.kylc.com/uprate/eur.html"),
            (LATEST, "ALIPAY", "USD", "alipay_settlement", "6.7198", "https://www.kylc.com/uprate/usd.html"),
        )

        payload = self.export()

        self.assertEqual(payload["generated_at"], "2026-10-01T00:00:05Z")
        self.assertEqual(payload["latest_date"], LATEST)
        self.assertEqual([item["id"] for item in payload["sources"]], ["BOC", "ALIPAY"])
        boc, alipay = payload["sources"]
        self.assertEqual(boc["rate_type"], "spot_sell")
        self.assertEqual(boc["label"], "中国银行")
        self.assertEqual(boc["rate_label"], "中国银行现汇卖出价")
        self.assertIn("中国银行外汇牌价", boc["description"])
        self.assertEqual(
            boc["rates"],
            {
                "EUR": {"rate": 7.6373, "date": LATEST},
                "USD": {"rate": 6.726, "date": LATEST},
            },
        )
        self.assertEqual(boc["website"], BOC_URL)
        self.assertEqual(alipay["source_url"], "https://www.kylc.com/uprate/eur.html")

    def test_skips_sources_not_updated_on_latest_date(self):
        self.insert(
            (LATEST, "BOC", "EUR", "spot_sell", "7.6373", BOC_URL),
            ("2026-09-20", "European Central Bank", "EUR", "reference", "7.6", "https://www.ecb.europa.eu/"),
        )

        payload = self.export()

        self.assertEqual([item["id"] for item in payload["sources"]], ["BOC"])

    def test_falls_back_when_preferred_type_is_stale(self):
        self.insert(
            ("2026-09-29", "BOC", "EUR", "spot_sell", "7.63", BOC_URL),
            (LATEST, "BOC", "EUR", "reference", "7.6215", BOC_URL),
        )

        (boc,) = self.export()["sources"]

        self.assertEqual(boc["rate_type"], "reference")
        self.assertEqual(boc["rates"], {"EUR": {"rate": 7.6215, "date": LATEST}})

    def test_history_covers_recent_window_in_date_order(self):
        latest = date.fromisoformat(LATEST)
        oldest_kept = (latest - timedelta(days=export_mcp_rates.HISTORY_DAYS - 1)).isoformat()
        too_old = (latest - timedelta(days=export_mcp_rates.HISTORY_DAYS)).isoformat()
        self.insert(
            (LATEST, "CIB", "EUR", "spot_sell", "7.6405", "https://example.com/cib"),
            (LATEST, "CIB", "USD", "spot_sell", "6.721", "https://example.com/cib"),
            (oldest_kept, "CIB", "EUR", "spot_sell", "7.5", "https://example.com/cib"),
            (too_old, "CIB", "EUR", "spot_sell", "7.4", "https://example.com/cib"),
            ("2026-09-15", "CIB", "EUR", "spot_sell", "invalid", "https://example.com/cib"),
        )

        (cib,) = self.export()["sources"]

        self.assertEqual(
            cib["history"],
            [
                {"date": oldest_kept, "EUR": 7.5},
                {"date": LATEST, "EUR": 7.6405, "USD": 6.721},
            ],
        )

    def test_unknown_source_uses_raw_names(self):
        self.insert((LATEST, "NEWBANK", "USD", "mystery", "6.7", "https://example.com/new"))

        (item,) = self.export()["sources"]

        self.assertEqual(item["label"], "NEWBANK")
        self.assertEqual(item["rate_label"], "NEWBANK mystery")
        self.assertEqual(item["description"], "")
        self.assertEqual(item["frequency"], "")

    def test_icbc_links_to_readable_rate_page(self):
        api_url = "http://papi.icbc.com.cn/exchanges/ns/getLatest"
        self.insert((LATEST, "ICBC", "EUR", "spot_sell", "7.6363", api_url))

        (icbc,) = self.export()["sources"]

        self.assertEqual(icbc["source_url"], api_url)
        self.assertEqual(icbc["website"], export_mcp_rates.SOURCES["ICBC"]["website"])

    def test_empty_database_exports_no_sources(self):
        payload = self.export()

        self.assertIsNone(payload["latest_date"])
        self.assertEqual(payload["sources"], [])

    def test_connection_is_read_only(self):
        with closing(export_mcp_rates.open_read_only(self.db_path)) as connection:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute(
                    "INSERT INTO exchange_rates VALUES ('2026-01-01', 'X', 'EUR', 'r', '1', 'u', 't')"
                )

    def test_main_writes_utf8_json(self):
        self.insert((LATEST, "BOC", "EUR", "spot_sell", "7.6373", BOC_URL))
        buffer = io.BytesIO()
        stdout = io.TextIOWrapper(buffer, encoding="ascii")

        with patch("sys.stdout", stdout):
            exit_code = export_mcp_rates.main(["--db", str(self.db_path)])

        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue().decode("utf-8"))
        self.assertEqual(payload["sources"][0]["label"], "中国银行")

    def test_main_reports_missing_database(self):
        missing = self.db_path.with_name("missing.sqlite")
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            exit_code = export_mcp_rates.main(["--db", str(missing)])

        self.assertEqual(exit_code, 1)
        self.assertIn("database not found", stderr.getvalue())
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
