from __future__ import annotations

import sqlite3
import unittest
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import ValidationError

from franchina_mcp.database import RatesRepository
from franchina_mcp.models import ExchangeRateInput, SaveExchangeRatesInput

FIRST_WRITE = datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc)
SECOND_WRITE = datetime(2026, 9, 2, 11, 0, tzinfo=timezone.utc)


def make_rate(**overrides: object) -> ExchangeRateInput:
    values: dict[str, object] = {
        "date": "2026-09-02",
        "source": "European Central Bank",
        "currency": "EUR",
        "rate_type": "reference",
        "rate": "7.863300",
        "source_url": "https://example.com/rates",
    }
    values.update(overrides)
    return ExchangeRateInput.model_validate(values)


class RatesRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / "rates.sqlite"
        self.repository = RatesRepository(self.database_path)

    def fetch_rows(self) -> list[tuple[str, ...]]:
        with closing(sqlite3.connect(self.database_path)) as connection:
            return connection.execute(
                """
                SELECT "date", source, currency, rate_type, rate, source_url, updated_at
                FROM exchange_rates
                ORDER BY "date", source, currency, rate_type
                """
            ).fetchall()

    def test_initialization_creates_only_required_columns(self) -> None:
        with closing(sqlite3.connect(self.database_path)) as connection:
            columns = [
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(exchange_rates)"
                ).fetchall()
            ]

        self.assertEqual(
            columns,
            [
                "date",
                "source",
                "currency",
                "rate_type",
                "rate",
                "source_url",
                "updated_at",
            ],
        )

    def test_new_rate_is_inserted(self) -> None:
        result = self.repository.save_exchange_rates(
            [make_rate()], updated_at=FIRST_WRITE
        )

        self.assertEqual(result.received, 1)
        self.assertEqual(result.inserted, 1)
        self.assertEqual(result.updated, 0)
        self.assertEqual(result.unchanged, 0)
        self.assertEqual(
            self.fetch_rows(),
            [
                (
                    "2026-09-02",
                    "European Central Bank",
                    "EUR",
                    "reference",
                    "7.8633",
                    "https://example.com/rates",
                    "2026-09-02T10:00:00Z",
                )
            ],
        )

    def test_identical_rate_does_not_write(self) -> None:
        self.repository.save_exchange_rates([make_rate()], updated_at=FIRST_WRITE)

        with closing(sqlite3.connect(self.database_path)) as observer:
            version_before = observer.execute("PRAGMA data_version").fetchone()[0]
            result = self.repository.save_exchange_rates(
                [make_rate()], updated_at=SECOND_WRITE
            )
            version_after = observer.execute("PRAGMA data_version").fetchone()[0]

        self.assertEqual(result.inserted, 0)
        self.assertEqual(result.updated, 0)
        self.assertEqual(result.unchanged, 1)
        self.assertEqual(version_after, version_before)
        self.assertEqual(self.fetch_rows()[0][-1], "2026-09-02T10:00:00Z")

    def test_changed_rate_updates_existing_row(self) -> None:
        self.repository.save_exchange_rates([make_rate()], updated_at=FIRST_WRITE)

        result = self.repository.save_exchange_rates(
            [make_rate(rate="7.9")], updated_at=SECOND_WRITE
        )

        self.assertEqual(result.inserted, 0)
        self.assertEqual(result.updated, 1)
        self.assertEqual(result.unchanged, 0)
        rows = self.fetch_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][4], "7.9")
        self.assertEqual(rows[0][-1], "2026-09-02T11:00:00Z")

    def test_changed_source_url_updates_existing_row(self) -> None:
        self.repository.save_exchange_rates([make_rate()], updated_at=FIRST_WRITE)

        result = self.repository.save_exchange_rates(
            [make_rate(source_url="https://example.com/revised")],
            updated_at=SECOND_WRITE,
        )

        self.assertEqual(result.updated, 1)
        self.assertEqual(len(self.fetch_rows()), 1)
        self.assertEqual(self.fetch_rows()[0][5], "https://example.com/revised")

    def test_each_unique_key_dimension_creates_a_distinct_row(self) -> None:
        rates = [
            make_rate(),
            make_rate(date="2026-09-03"),
            make_rate(source="Banque de France"),
            make_rate(currency="USD"),
            make_rate(rate_type="buy"),
        ]

        result = self.repository.save_exchange_rates(rates, updated_at=FIRST_WRITE)

        self.assertEqual(result.inserted, 5)
        self.assertEqual(len(self.fetch_rows()), 5)


class ExchangeRateInputTests(unittest.TestCase):
    def test_accepts_only_supported_foreign_currencies(self) -> None:
        self.assertEqual(make_rate(currency="EUR").currency, "EUR")
        self.assertEqual(make_rate(currency="USD").currency, "USD")

        for currency in ("CNY", "GBP"):
            with self.subTest(currency=currency), self.assertRaises(ValidationError):
                make_rate(currency=currency)

    def test_rejects_invalid_or_unexpected_fields(self) -> None:
        invalid_overrides = [
            {"date": "2026-9-2"},
            {"source": ""},
            {"currency": "eur"},
            {"currency": "EURO"},
            {"rate_type": "cash buy"},
            {"rate": "0"},
            {"source_url": "ftp://example.com/rates"},
            {"unexpected": "value"},
        ]

        for overrides in invalid_overrides:
            with self.subTest(overrides=overrides):
                values: dict[str, object] = {
                    "date": "2026-09-02",
                    "source": "European Central Bank",
                    "currency": "EUR",
                    "rate_type": "reference",
                    "rate": "7.8633",
                    "source_url": "https://example.com/rates",
                }
                values.update(overrides)
                with self.assertRaises(ValidationError):
                    ExchangeRateInput.model_validate(values)

    def test_batch_rejects_duplicate_keys(self) -> None:
        rate = make_rate()

        with self.assertRaises(ValidationError):
            SaveExchangeRatesInput(rates=[rate, rate])

    def test_batch_rejects_empty_input(self) -> None:
        with self.assertRaises(ValidationError):
            SaveExchangeRatesInput(rates=[])

    def test_accepts_date_objects_without_coercing_datetime(self) -> None:
        parsed = make_rate(date=date(2026, 9, 2))

        self.assertEqual(parsed.date, date(2026, 9, 2))
        with self.assertRaises(ValidationError):
            make_rate(date=datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc))
