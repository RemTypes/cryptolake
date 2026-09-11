"""Unit tests for Phase 2 exchange adapters with mocked network responses."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from cryptolake.sources import (
    BybitSource,
    CoinbaseSource,
    CryptoCompareSource,
    KrakenSource,
    OKXSource,
)


@pytest.mark.asyncio
async def test_coinbase_normalisation_and_lhocv_parsing() -> None:
    source = CoinbaseSource()
    assert source.normalise_symbol("BTC", "USD") == "BTC-USD"
    assert source.normalise_symbol("ETH", "USDT") == "ETH-USDT"

    # Coinbase sends [time_s, low, high, open, close, volume] descending
    mock_candles = [
        [1700003600, 39900.0, 40200.0, 40000.0, 40150.0, 50.0],
        [1700000000, 39800.0, 40100.0, 39900.0, 40000.0, 45.0],
    ]

    with patch.object(source, "_request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_candles
        start = datetime(2023, 11, 14, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 11, 15, 0, 0, tzinfo=timezone.utc)

        df = await source.fetch_ohlcv("BTC", "USD", "1h", start, end)

        assert df.height == 2
        # Verify columns remapped properly: open should be 39900.0 on row 0, 40000.0 on row 1
        assert df["open"].to_list() == [39900.0, 40000.0]
        assert df["close"].to_list() == [40000.0, 40150.0]
        assert df["high"].to_list() == [40100.0, 40200.0]
        assert df["low"].to_list() == [39800.0, 39900.0]
        assert df["exchange"][0] == "coinbase"


@pytest.mark.asyncio
async def test_kraken_normalisation_and_ohlc_parsing() -> None:
    source = KrakenSource()
    assert source.normalise_symbol("BTC", "USD") == "XBTUSD"
    assert source.normalise_symbol("ETH", "USD") == "ETHUSD"

    mock_res = {
        "error": [],
        "result": {
            "XXBTZUSD": [
                [1700000000, "39900.0", "40100.0", "39800.0", "40000.0", "39950.0", "12.5", 42]
            ],
            "last": 1700003600,
        },
    }

    with patch.object(source, "_request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_res
        start = datetime(2023, 11, 14, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 11, 15, 0, 0, tzinfo=timezone.utc)

        df = await source.fetch_ohlcv("BTC", "USD", "1h", start, end)
        assert df.height == 1
        assert df["open"][0] == 39900.0
        assert df["trade_count"][0] == 42
        assert df["exchange"][0] == "kraken"


@pytest.mark.asyncio
async def test_okx_normalisation_and_parsing() -> None:
    source = OKXSource()
    assert source.normalise_symbol("BTC", "USDT") == "BTC-USDT"

    mock_res = {
        "code": "0",
        "data": [
            [
                "1700000000000",
                "39900.0",
                "40100.0",
                "39800.0",
                "40000.0",
                "15.0",
                "600000.0",
                "600000.0",
                "1",
            ]
        ],
    }

    with patch.object(source, "_request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_res
        start = datetime(2023, 11, 14, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 11, 15, 0, 0, tzinfo=timezone.utc)

        df = await source.fetch_ohlcv("BTC", "USDT", "1h", start, end)
        assert df.height == 1
        assert df["volume_base"][0] == 15.0
        assert df["exchange"][0] == "okx"


@pytest.mark.asyncio
async def test_bybit_normalisation_and_parsing() -> None:
    source = BybitSource()
    assert source.normalise_symbol("BTC", "USDT") == "BTCUSDT"

    mock_res = {
        "retCode": 0,
        "result": {
            "list": [
                ["1700000000000", "39900.0", "40100.0", "39800.0", "40000.0", "10.0", "400000.0"]
            ]
        },
    }

    with patch.object(source, "_request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_res
        start = datetime(2023, 11, 14, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 11, 15, 0, 0, tzinfo=timezone.utc)

        df = await source.fetch_ohlcv("BTC", "USDT", "1h", start, end)
        assert df.height == 1
        assert df["close"][0] == 40000.0
        assert df["exchange"][0] == "bybit"


@pytest.mark.asyncio
async def test_cryptocompare_normalisation_and_parsing() -> None:
    source = CryptoCompareSource()
    assert source.normalise_symbol("BTC", "USD") == "BTC/USD"

    mock_res = {
        "Response": "Success",
        "Data": {
            "Data": [
                {
                    "time": 1700000000,
                    "open": 39900.0,
                    "high": 40100.0,
                    "low": 39800.0,
                    "close": 40000.0,
                    "volumefrom": 8.0,
                    "volumeto": 320000.0,
                }
            ]
        },
    }

    with patch.object(source, "_request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_res
        start = datetime(2023, 11, 14, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 11, 15, 0, 0, tzinfo=timezone.utc)

        df = await source.fetch_ohlcv("BTC", "USD", "1h", start, end)
        assert df.height == 1
        assert df["volume_base"][0] == 8.0
        assert df["exchange"][0] == "cryptocompare"
