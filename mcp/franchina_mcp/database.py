from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from .models import ExchangeRateInput, SaveExchangeRatesResult

CREATE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS exchange_rates (
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


class RatesRepository:
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
        return connection

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            connection.execute(CREATE_SCHEMA_SQL)

    def save_exchange_rates(
        self,
        rates: Sequence[ExchangeRateInput],
        *,
        updated_at: datetime | None = None,
    ) -> SaveExchangeRatesResult:
        timestamp = _format_timestamp(updated_at or datetime.now(timezone.utc))
        inserted = 0
        updated = 0
        unchanged = 0

        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            for item in rates:
                rate_value = _format_decimal(item.rate)
                source_url = str(item.source_url)
                existing = connection.execute(
                    """
                    SELECT rate, source_url
                    FROM exchange_rates
                    WHERE "date" = ? AND source = ? AND currency = ? AND rate_type = ?
                    """,
                    item.unique_key,
                ).fetchone()

                if existing is None:
                    connection.execute(
                        """
                        INSERT INTO exchange_rates (
                            "date", source, currency, rate_type, rate, source_url, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (*item.unique_key, rate_value, source_url, timestamp),
                    )
                    inserted += 1
                elif existing == (rate_value, source_url):
                    unchanged += 1
                else:
                    connection.execute(
                        """
                        UPDATE exchange_rates
                        SET rate = ?, source_url = ?, updated_at = ?
                        WHERE "date" = ? AND source = ? AND currency = ? AND rate_type = ?
                        """,
                        (rate_value, source_url, timestamp, *item.unique_key),
                    )
                    updated += 1

            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

        return SaveExchangeRatesResult(
            received=len(rates),
            inserted=inserted,
            updated=updated,
            unchanged=unchanged,
        )


def _format_decimal(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("updated_at must include a timezone")
    utc_value = value.astimezone(timezone.utc)
    timespec = "microseconds" if utc_value.microsecond else "seconds"
    return utc_value.isoformat(timespec=timespec).replace("+00:00", "Z")
