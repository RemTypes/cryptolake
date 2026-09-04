"""Canonical 24-hour ticker snapshot schema.

Captures the current state of a trading pair: last price, best bid/ask, and
24-hour aggregate statistics.
"""

from __future__ import annotations

import polars as pl
from polars.datatypes import DataType, DataTypeClass
from polars.exceptions import SchemaError

_TICKER_FIELDS: dict[str, DataType | DataTypeClass] = {
    "timestamp": pl.Datetime("ms", time_zone="UTC"),
    "exchange": pl.Categorical(),
    "base": pl.Utf8,
    "quote": pl.Utf8,
    "last_price": pl.Float64,
    "bid_price": pl.Float64,
    "ask_price": pl.Float64,
    "high_24h": pl.Float64,
    "low_24h": pl.Float64,
    "volume_24h_base": pl.Float64,
    "volume_24h_quote": pl.Float64,
    "price_change_pct": pl.Float64,
}

TICKER_SCHEMA = pl.Schema(_TICKER_FIELDS)
"""Polars schema for canonical 24h ticker snapshots.

``price_change_pct`` is nullable — some exchanges don't provide it directly.
"""

TICKER_COLUMNS: list[str] = list(TICKER_SCHEMA.names())
"""Ordered list of column names in the canonical ticker schema."""


def validate_ticker(df: pl.DataFrame) -> pl.DataFrame:
    """Validate and cast a DataFrame to the canonical ticker schema."""
    missing = set(TICKER_COLUMNS) - set(df.columns)
    if missing:
        msg = f"Missing required ticker columns: {missing}"
        raise SchemaError(msg)

    return df.select(TICKER_COLUMNS).cast(TICKER_SCHEMA)
