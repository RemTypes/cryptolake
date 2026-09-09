"""Tests for the FastAPI application routes."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import polars as pl
import pytest
from fastapi.testclient import TestClient

from cryptolake.api.app import create_app
from cryptolake.api.deps import get_data_dir
from cryptolake.pipeline import storage


@pytest.fixture
def test_data_dir(tmp_path: Path) -> Path:
    """Populate temporary data dir with sample OHLCV and tickers."""
    ohlcv_df = pl.DataFrame(
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
    storage.write_ohlcv(ohlcv_df, tmp_path)

    ticker_df = pl.DataFrame(
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
    storage.write_tickers(ticker_df, tmp_path)

    return tmp_path


@pytest.fixture
def client(test_data_dir: Path) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_data_dir] = lambda: test_data_dir
    return TestClient(app)


def test_root(client: TestClient) -> None:
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "CryptoLake"


def test_health(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_list_ohlcv_exchanges(client: TestClient) -> None:
    res = client.get("/api/v1/ohlcv/exchanges")
    assert res.status_code == 200
    assert "binance" in res.json()


def test_query_ohlcv_json(client: TestClient) -> None:
    res = client.get("/api/v1/ohlcv/binance/BTC-USDT?interval=1h")
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) == 2
    assert rows[0]["open"] == 42000.0


def test_query_ohlcv_csv(client: TestClient) -> None:
    res = client.get("/api/v1/ohlcv/binance/BTC-USDT?interval=1h&format=csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "open,high,low,close" in res.text


def test_query_ohlcv_not_found(client: TestClient) -> None:
    res = client.get("/api/v1/ohlcv/binance/ETH-USDT?interval=1h")
    assert res.status_code == 404


def test_tickers(client: TestClient) -> None:
    res = client.get("/api/v1/tickers")
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) == 1
    assert rows[0]["last_price"] == 42250.0


def test_metadata_symbols(client: TestClient) -> None:
    res = client.get("/api/v1/metadata/symbols")
    assert res.status_code == 200
    data = res.json()
    assert "BTC-USDT" in data
    assert "binance" in data["BTC-USDT"]


def test_download_parquet(client: TestClient) -> None:
    res = client.get("/api/v1/download/ohlcv/binance/BTC-USDT")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/vnd.apache.parquet"
    assert len(res.content) > 0
