from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    field_validator,
    model_validator,
)

CurrencyCode = Annotated[
    Literal["EUR", "USD"],
    Field(
        description=(
            "Foreign currency priced in CNY; phase one accepts only EUR or USD."
        )
    ),
]
RateType = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=32,
        pattern=r"^[a-z][a-z0-9_]*$",
    ),
]
SourceName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]
PositiveRate = Annotated[
    Decimal,
    Field(
        gt=Decimal(0),
        max_digits=24,
        decimal_places=12,
        allow_inf_nan=False,
        description=(
            "Normalized CNY price of exactly one unit: 1 currency = rate CNY. "
            "Divide source quotes for 100 foreign-currency units by 100 before "
            "submission."
        ),
    ),
]


class ExchangeRateInput(BaseModel):
    """A normalized EUR/USD quote where 1 currency = rate CNY."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    date: date
    source: SourceName
    currency: CurrencyCode
    rate_type: RateType
    rate: PositiveRate
    source_url: HttpUrl

    @field_validator("date", mode="before")
    @classmethod
    def validate_date_format(cls, value: object) -> object:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return value
        raise ValueError("date must use YYYY-MM-DD format")

    @field_validator("source")
    @classmethod
    def reject_control_characters(cls, value: str) -> str:
        if any(unicodedata.category(character).startswith("C") for character in value):
            raise ValueError("source contains a control character")
        return value

    @property
    def unique_key(self) -> tuple[str, str, str, str]:
        return (
            self.date.isoformat(),
            self.source,
            self.currency,
            self.rate_type,
        )


ExchangeRateBatch = Annotated[
    list[ExchangeRateInput],
    Field(min_length=1, max_length=200),
]


class SaveExchangeRatesInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rates: ExchangeRateBatch

    @model_validator(mode="after")
    def reject_duplicate_keys(self) -> SaveExchangeRatesInput:
        seen: set[tuple[str, str, str, str]] = set()
        for rate in self.rates:
            if rate.unique_key in seen:
                raise ValueError(
                    "rates contains duplicate date/source/currency/rate_type keys"
                )
            seen.add(rate.unique_key)
        return self


class SaveExchangeRatesResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    received: int = Field(ge=0)
    inserted: int = Field(ge=0)
    updated: int = Field(ge=0)
    unchanged: int = Field(ge=0)
