"""Tests for the Parquet storage layer."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import polars as pl
import pytest

from cryptolake.pipeline import storage


@pytest.fixture
def sample_ohlcv_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "timestamp": [
                datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc),
            ],
            "exchange": ["binance", "binance"],
            "base": ["BTC", "BTC"],
            "quote": ["USDT", "USDT"],
            "interval": ["1h", "1h"],
            "open": [42000.0, 42100.0],
            "high": [42200.0, 42300.0],
            "low": [41900.0, 42000.0],
            "close": [42100.0, 42250.0],
            "volume_base": [15.5, 12.3],
            "volume_quote": [650000.0, 520000.0],
            "trade_count": [120, 110],
            "vwap": [42050.0, 42180.0],
            "taker_buy_volume": [8.0, 6.5],
        }
    )


@pytest.fixture
def sample_ticker_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "timestamp": [datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)],
            "exchange": ["binance"],
            "base": ["BTC"],
            "quote": ["USDT"],
            "last_price": [42250.0],
            "bid_price": [42240.0],
            "ask_price": [42260.0],
            "high_24h": [43000.0],
            "low_24h": [41500.0],
            "volume_24h_base": [1500.0],
            "volume_24h_quote": [63000000.0],
            "price_change_pct": [2.5],
        }
    )


def test_write_and_read_ohlcv(tmp_path: Path, sample_ohlcv_df: pl.DataFrame) -> None:
    out_dir = storage.write_ohlcv(sample_ohlcv_df, tmp_path)
    assert out_dir.exists()

    # Read back
    lf = storage.read_ohlcv(tmp_path, exchange="binance", base="BTC", quote="USDT", interval="1h")
    df = lf.collect()
    assert df.height == 2
    assert df["open"].to_list() == [42000.0, 42100.0]


def test_write_and_read_tickers(tmp_path: Path, sample_ticker_df: pl.DataFrame) -> None:
    out_dir = storage.write_tickers(sample_ticker_df, tmp_path)
    assert out_dir.exists()

    lf = storage.read_tickers(tmp_path, exchange="binance")
    df = lf.collect()
    assert df.height == 1
    assert df["last_price"].to_list() == [42250.0]


def test_list_available_datasets(tmp_path: Path, sample_ohlcv_df: pl.DataFrame) -> None:
    storage.write_ohlcv(sample_ohlcv_df, tmp_path)
    datasets = storage.list_available_datasets(tmp_path)
    assert "ohlcv" in datasets
    assert len(datasets["ohlcv"]) == 1
    assert datasets["ohlcv"][0]["exchange"] == "binance"
    assert datasets["ohlcv"][0]["symbol"] == "BTC-USDT"
