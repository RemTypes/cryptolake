"""Tests for data validation."""

from __future__ import annotations

from datetime import datetime, timezone

import polars as pl

from cryptolake.pipeline.validate import validate_ohlcv, validate_ticker, validate_trades


def _make_ohlcv(**overrides: object) -> pl.DataFrame:
    """Create a minimal valid OHLCV DataFrame with optional overrides."""
    defaults = {
        "timestamp": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
        "exchange": ["binance"],
        "base": ["BTC"],
        "quote": ["USDT"],
        "interval": ["1h"],
        "open": [50000.0],
        "high": [51000.0],
        "low": [49000.0],
        "close": [50500.0],
        "volume_base": [100.0],
        "volume_quote": [5000000.0],
        "trade_count": [1000],
        "vwap": [50200.0],
        "taker_buy_volume": [60.0],
    }
    defaults.update(overrides)  # type: ignore[arg-type]
    return pl.DataFrame(defaults)


class TestValidateOHLCV:
    def test_valid_data_passes(self) -> None:
        df = _make_ohlcv()
        result = validate_ohlcv(df)
        assert result.is_valid
        assert result.errors == []

    def test_high_below_low_fails(self) -> None:
        df = _make_ohlcv(high=[48000.0], low=[49000.0])
        result = validate_ohlcv(df)
        assert not result.is_valid
        assert any("invalid high" in e for e in result.errors)

    def test_negative_price_fails(self) -> None:
        df = _make_ohlcv(open=[-1.0])
        result = validate_ohlcv(df)
        assert not result.is_valid

    def test_empty_dataframe_is_valid(self) -> None:
        df = _make_ohlcv().clear()
        result = validate_ohlcv(df)
        assert result.is_valid
        assert result.row_count == 0


class TestValidateTrades:
    def test_valid_trade_passes(self) -> None:
        df = pl.DataFrame(
            {
                "timestamp": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
                "exchange": ["binance"],
                "base": ["BTC"],
                "quote": ["USDT"],
                "trade_id": ["123"],
                "price": [50000.0],
                "quantity": [0.1],
                "side": ["buy"],
                "is_maker": [True],
            }
        )
        result = validate_trades(df)
        assert result.is_valid

    def test_invalid_side_fails(self) -> None:
        df = pl.DataFrame(
            {
                "timestamp": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
                "exchange": ["binance"],
                "base": ["BTC"],
                "quote": ["USDT"],
                "trade_id": ["123"],
                "price": [50000.0],
                "quantity": [0.1],
                "side": ["unknown"],
                "is_maker": [True],
            }
        )
        result = validate_trades(df)
        assert not result.is_valid


class TestValidateTicker:
    def test_valid_ticker_passes(self) -> None:
        df = pl.DataFrame(
            {
                "timestamp": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
                "exchange": ["binance"],
                "base": ["BTC"],
                "quote": ["USDT"],
                "last_price": [50000.0],
                "bid_price": [49999.0],
                "ask_price": [50001.0],
                "high_24h": [51000.0],
                "low_24h": [49000.0],
                "volume_24h_base": [1000.0],
                "volume_24h_quote": [50000000.0],
                "price_change_pct": [1.5],
            }
        )
        result = validate_ticker(df)
        assert result.is_valid

    def test_crossed_market_warns(self) -> None:
        df = pl.DataFrame(
            {
                "timestamp": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
                "exchange": ["binance"],
                "base": ["BTC"],
                "quote": ["USDT"],
                "last_price": [50000.0],
                "bid_price": [50002.0],
                "ask_price": [49999.0],
                "high_24h": [51000.0],
                "low_24h": [49000.0],
                "volume_24h_base": [1000.0],
                "volume_24h_quote": [50000000.0],
                "price_change_pct": [1.5],
            }
        )
        result = validate_ticker(df)
        assert result.is_valid  # crossed markets are warnings, not errors
        assert len(result.warnings) > 0
