"""Asset and exchange metadata schemas.

Stores reference data about exchanges (available pairs, fee tiers, rate limits)
and assets (name, symbol, market cap rank) obtained from aggregator APIs.
"""

from __future__ import annotations

import polars as pl
from polars.datatypes import DataType, DataTypeClass

_ASSET_METADATA_FIELDS: dict[str, DataType | DataTypeClass] = {
    "coingecko_id": pl.Utf8,
    "symbol": pl.Utf8,
    "name": pl.Utf8,
    "market_cap_rank": pl.UInt32,
    "market_cap_usd": pl.Float64,
    "current_price_usd": pl.Float64,
    "total_volume_24h_usd": pl.Float64,
    "circulating_supply": pl.Float64,
    "total_supply": pl.Float64,
    "ath_usd": pl.Float64,
    "ath_date": pl.Datetime("ms", time_zone="UTC"),
    "last_updated": pl.Datetime("ms", time_zone="UTC"),
}

ASSET_METADATA_SCHEMA = pl.Schema(_ASSET_METADATA_FIELDS)
"""Polars schema for asset metadata (sourced from CoinGecko)."""


_EXCHANGE_PAIR_FIELDS: dict[str, DataType | DataTypeClass] = {
    "exchange": pl.Categorical(),
    "native_symbol": pl.Utf8,
    "base": pl.Utf8,
    "quote": pl.Utf8,
    "is_active": pl.Boolean,
    "last_updated": pl.Datetime("ms", time_zone="UTC"),
}

EXCHANGE_PAIR_SCHEMA = pl.Schema(_EXCHANGE_PAIR_FIELDS)
"""Polars schema for the mapping of exchange-native symbols to canonical pairs."""

ASSET_METADATA_COLUMNS: list[str] = list(ASSET_METADATA_SCHEMA.names())
EXCHANGE_PAIR_COLUMNS: list[str] = list(EXCHANGE_PAIR_SCHEMA.names())
