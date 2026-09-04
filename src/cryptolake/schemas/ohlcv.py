"""Canonical OHLCV (candlestick) schema.

Every exchange's candle data — regardless of native column ordering, timestamp
units, or sort direction — gets normalised into this schema before being written
to Parquet.
"""

from __future__ import annotations

import polars as pl
from polars.datatypes import DataType, DataTypeClass
from polars.exceptions import SchemaError

_OHLCV_FIELDS: dict[str, DataType | DataTypeClass] = {
    "timestamp": pl.Datetime("ms", time_zone="UTC"),
    "exchange": pl.Categorical(),
    "base": pl.Utf8,
    "quote": pl.Utf8,
    "interval": pl.Utf8,
    "open": pl.Float64,
    "high": pl.Float64,
    "low": pl.Float64,
    "close": pl.Float64,
    "volume_base": pl.Float64,
    "volume_quote": pl.Float64,
    "trade_count": pl.UInt32,
    "vwap": pl.Float64,
    "taker_buy_volume": pl.Float64,
}

OHLCV_SCHEMA = pl.Schema(_OHLCV_FIELDS)
"""Polars schema for canonical OHLCV data.

Nullable columns (``trade_count``, ``vwap``, ``taker_buy_volume``) will contain
``null`` when the source exchange does not provide the field.
"""

OHLCV_COLUMNS: list[str] = list(OHLCV_SCHEMA.names())
"""Ordered list of column names in the canonical OHLCV schema."""


def validate_ohlcv(df: pl.DataFrame) -> pl.DataFrame:
    """Validate and cast a DataFrame to the canonical OHLCV schema.

    Raises ``SchemaError`` if required columns are missing or types cannot
    be cast.
    """
    # Ensure all required columns exist
    missing = set(OHLCV_COLUMNS) - set(df.columns)
    if missing:
        msg = f"Missing required OHLCV columns: {missing}"
        raise SchemaError(msg)

    # Select in canonical order and cast types
    return df.select(OHLCV_COLUMNS).cast(OHLCV_SCHEMA)
