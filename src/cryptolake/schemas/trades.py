"""Canonical trade (individual execution) schema.

Normalises trade data from all exchanges into a single format with consistent
side labelling, string trade IDs, and millisecond UTC timestamps.
"""

from __future__ import annotations

import polars as pl
from polars.datatypes import DataType, DataTypeClass
from polars.exceptions import SchemaError

_TRADE_FIELDS: dict[str, DataType | DataTypeClass] = {
    "timestamp": pl.Datetime("ms", time_zone="UTC"),
    "exchange": pl.Categorical(),
    "base": pl.Utf8,
    "quote": pl.Utf8,
    "trade_id": pl.Utf8,
    "price": pl.Float64,
    "quantity": pl.Float64,
    "side": pl.Categorical(),
    "is_maker": pl.Boolean,
}

TRADE_SCHEMA = pl.Schema(_TRADE_FIELDS)
"""Polars schema for canonical trade data.

``side`` is always ``"buy"`` or ``"sell"`` (taker side).
``is_maker`` is nullable — not all exchanges expose this field.
``trade_id`` is always a string for cross-exchange universality.
"""

TRADE_COLUMNS: list[str] = list(TRADE_SCHEMA.names())
"""Ordered list of column names in the canonical trade schema."""


def validate_trades(df: pl.DataFrame) -> pl.DataFrame:
    """Validate and cast a DataFrame to the canonical trade schema."""
    missing = set(TRADE_COLUMNS) - set(df.columns)
    if missing:
        msg = f"Missing required trade columns: {missing}"
        raise SchemaError(msg)

    return df.select(TRADE_COLUMNS).cast(TRADE_SCHEMA)
