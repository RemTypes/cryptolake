"""Tests for the cross-exchange price comparison and arbitrage endpoint."""

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
def multi_exchange_data_dir(tmp_path: Path) -> Path:
    """Populate temporary data dir with multi-exchange ticker quotes to test arbitrage detection."""
    # Binance: bid 42,000, ask 42,020, last 42,010
    # Coinbase: bid 42,050, ask 42,070, last 42,060
    # Here, Coinbase bid (42,050) > Binance ask (42,020) -> 30 USD gross arbitrage!
    tickers_df = pl.DataFrame(
        {
            "timestamp": [
                datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            ],
            "exchange": ["binance", "coinbase"],
            "base": ["BTC", "BTC"],
            "quote": ["USDT", "USDT"],
            "last_price": [42010.0, 42060.0],
            "bid_price": [42000.0, 42050.0],
            "ask_price": [42020.0, 42070.0],
            "high_24h": [42500.0, 42550.0],
            "low_24h": [41800.0, 41850.0],
            "volume_24h_base": [1200.0, 950.0],
            "volume_24h_quote": [50400000.0, 39900000.0],
            "price_change_pct": [1.2, 1.3],
        }
    )
    storage.write_tickers(tickers_df, tmp_path)
    return tmp_path


@pytest.fixture
def compare_client(multi_exchange_data_dir: Path) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_data_dir] = lambda: multi_exchange_data_dir
    return TestClient(app)


def test_compare_prices_success(compare_client: TestClient) -> None:
    res = compare_client.get("/api/v1/compare/BTC-USDT")
    assert res.status_code == 200
    data = res.json()

    assert data["symbol"] == "BTC-USDT"
    assert data["venue_count"] == 2

    summary = data["spread_summary"]
    assert summary["min_price"] == 42010.0
    assert summary["max_price"] == 42060.0
    assert summary["spread_abs"] == 50.0
    assert summary["spread_bps"] > 0

    # Arbitrage check: Coinbase bid (42050) > Binance ask (42020)
    assert summary["arbitrage_opportunity"] is True
    assert summary["gross_arbitrage_bps"] > 0
    assert summary["best_buy_venue"] == "binance"
    assert summary["best_sell_venue"] == "coinbase"


def test_compare_invalid_symbol(compare_client: TestClient) -> None:
    res = compare_client.get("/api/v1/compare/INVALID")
    assert res.status_code == 400


def test_compare_not_found(compare_client: TestClient) -> None:
    res = compare_client.get("/api/v1/compare/SOL-USDC")
    assert res.status_code == 404
