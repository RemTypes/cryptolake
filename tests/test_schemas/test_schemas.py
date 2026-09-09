"""Tests for the unified Parquet schemas."""

from __future__ import annotations

import polars as pl
import pytest
from polars.exceptions import SchemaError

from cryptolake.schemas.ohlcv import OHLCV_COLUMNS, validate_ohlcv
from cryptolake.schemas.ticker import TICKER_COLUMNS, validate_ticker
from cryptolake.schemas.trades import TRADE_COLUMNS, validate_trades


class TestOHLCVSchema:
    """Tests for the canonical OHLCV schema."""

    def test_schema_has_expected_columns(self) -> None:
        expected = [
            "timestamp",
            "exchange",
            "base",
            "quote",
            "interval",
            "open",
            "high",
            "low",
            "close",
            "volume_base",
            "volume_quote",
            "trade_count",
            "vwap",
            "taker_buy_volume",
        ]
        assert expected == OHLCV_COLUMNS

    def test_validate_rejects_missing_columns(self) -> None:
        df = pl.DataFrame({"timestamp": [], "exchange": []})
        with pytest.raises(SchemaError, match="Missing required"):
            validate_ohlcv(df)


class TestTradeSchema:
    """Tests for the canonical trade schema."""

    def test_schema_has_expected_columns(self) -> None:
        expected = [
            "timestamp",
            "exchange",
            "base",
            "quote",
            "trade_id",
            "price",
            "quantity",
            "side",
            "is_maker",
        ]
        assert expected == TRADE_COLUMNS

    def test_validate_rejects_missing_columns(self) -> None:
        df = pl.DataFrame({"timestamp": [], "price": []})
        with pytest.raises(SchemaError, match="Missing required"):
            validate_trades(df)


class TestTickerSchema:
    """Tests for the canonical ticker schema."""

    def test_schema_has_expected_columns(self) -> None:
        expected = [
            "timestamp",
            "exchange",
            "base",
            "quote",
            "last_price",
            "bid_price",
            "ask_price",
            "high_24h",
            "low_24h",
            "volume_24h_base",
            "volume_24h_quote",
            "price_change_pct",
        ]
        assert expected == TICKER_COLUMNS

    def test_validate_rejects_missing_columns(self) -> None:
        df = pl.DataFrame({"timestamp": [], "last_price": []})
        with pytest.raises(SchemaError, match="Missing required"):
            validate_ticker(df)
