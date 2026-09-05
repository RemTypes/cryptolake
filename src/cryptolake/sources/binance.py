"""Binance Spot API v3 data source adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import polars as pl

from .base import BaseSource


class BinanceSource(BaseSource):
    name = "binance"
    BASE_URL = "https://api.binance.com"

    def normalise_symbol(self, base: str, quote: str) -> str:
        return f"{base.upper()}{quote.upper()}"

    def _convert_interval(self, interval: str) -> str:
        # Simplistic mapping assuming interval is like '1m', '1h', '1d'
        return interval

    async def fetch_ohlcv(
        self,
        base: str,
        quote: str,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> pl.DataFrame:
        symbol = self.normalise_symbol(base, quote)
        binance_interval = self._convert_interval(interval)

        all_data: list[Any] = []
        current_start = int(start.replace(tzinfo=timezone.utc).timestamp() * 1000)
        end_ts = int(end.replace(tzinfo=timezone.utc).timestamp() * 1000)

        while current_start < end_ts:
            params = {
                "symbol": symbol,
                "interval": binance_interval,
                "startTime": current_start,
                "endTime": end_ts,
                "limit": 1000,
            }

            data = await self._request(
                "GET", f"{self.BASE_URL}/api/v3/klines", params=params, weight=2
            )
            if not data:
                break

            all_data.extend(data)

            last_ts = data[-1][0]
            if last_ts >= end_ts or len(data) < 1000:
                break

            current_start = last_ts + 1

        if not all_data:
            return pl.DataFrame(
                schema={
                    "timestamp": pl.Datetime("ms", "UTC"),
                    "exchange": pl.String,
                    "base": pl.String,
                    "quote": pl.String,
                    "interval": pl.String,
                    "open": pl.Float64,
                    "high": pl.Float64,
                    "low": pl.Float64,
                    "close": pl.Float64,
                    "volume_base": pl.Float64,
                    "volume_quote": pl.Float64,
                    "trade_count": pl.Int64,
                    "vwap": pl.Float64,
                    "taker_buy_volume": pl.Float64,
                }
            )

        df = pl.DataFrame(
            all_data,
            schema=[
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base_asset_volume",
                "taker_buy_quote_asset_volume",
                "ignore",
            ],
            orient="row",
        )

        return df.select(
            [
                pl.col("open_time").cast(pl.Datetime("ms", "UTC")).alias("timestamp"),
                pl.lit(self.name).alias("exchange"),
                pl.lit(base).alias("base"),
                pl.lit(quote).alias("quote"),
                pl.lit(interval).alias("interval"),
                pl.col("open").cast(pl.Float64),
                pl.col("high").cast(pl.Float64),
                pl.col("low").cast(pl.Float64),
                pl.col("close").cast(pl.Float64),
                pl.col("volume").cast(pl.Float64).alias("volume_base"),
                pl.col("quote_asset_volume").cast(pl.Float64).alias("volume_quote"),
                pl.col("number_of_trades").cast(pl.Int64).alias("trade_count"),
                (
                    pl.col("quote_asset_volume").cast(pl.Float64)
                    / pl.col("volume").cast(pl.Float64)
                ).alias("vwap"),
                pl.col("taker_buy_base_asset_volume").cast(pl.Float64).alias("taker_buy_volume"),
            ]
        )

    async def fetch_trades(self, base: str, quote: str, limit: int = 500) -> pl.DataFrame:
        symbol = self.normalise_symbol(base, quote)

        # limit max 1000
        limit = min(limit, 1000)

        params = {
            "symbol": symbol,
            "limit": limit,
        }

        data = await self._request(
            "GET", f"{self.BASE_URL}/api/v3/trades", params=params, weight=10
        )

        if not data:
            return pl.DataFrame(
                schema={
                    "timestamp": pl.Datetime("ms", "UTC"),
                    "exchange": pl.String,
                    "base": pl.String,
                    "quote": pl.String,
                    "trade_id": pl.String,
                    "price": pl.Float64,
                    "quantity": pl.Float64,
                    "side": pl.String,
                    "is_maker": pl.Boolean,
                }
            )

        df = pl.DataFrame(data)

        return df.select(
            [
                pl.col("time").cast(pl.Datetime("ms", "UTC")).alias("timestamp"),
                pl.lit(self.name).alias("exchange"),
                pl.lit(base).alias("base"),
                pl.lit(quote).alias("quote"),
                pl.col("id").cast(pl.String).alias("trade_id"),
                pl.col("price").cast(pl.Float64),
                pl.col("qty").cast(pl.Float64).alias("quantity"),
                pl.when(pl.col("isBuyerMaker"))
                .then(pl.lit("sell"))
                .otherwise(pl.lit("buy"))
                .alias("side"),
                pl.col("isBuyerMaker").alias("is_maker"),
            ]
        )

    async def fetch_ticker(self, base: str, quote: str) -> pl.DataFrame:
        symbol = self.normalise_symbol(base, quote)
        params = {"symbol": symbol}

        data = await self._request(
            "GET", f"{self.BASE_URL}/api/v3/ticker/24hr", params=params, weight=2
        )

        df = pl.DataFrame([data])

        return df.select(
            [
                pl.col("closeTime").cast(pl.Datetime("ms", "UTC")).alias("timestamp"),
                pl.lit(self.name).alias("exchange"),
                pl.lit(base).alias("base"),
                pl.lit(quote).alias("quote"),
                pl.col("lastPrice").cast(pl.Float64).alias("last_price"),
                pl.col("bidPrice").cast(pl.Float64).alias("bid_price"),
                pl.col("askPrice").cast(pl.Float64).alias("ask_price"),
                pl.col("highPrice").cast(pl.Float64).alias("high_24h"),
                pl.col("lowPrice").cast(pl.Float64).alias("low_24h"),
                pl.col("volume").cast(pl.Float64).alias("volume_24h_base"),
                pl.col("quoteVolume").cast(pl.Float64).alias("volume_24h_quote"),
                pl.col("priceChangePercent").cast(pl.Float64).alias("price_change_pct"),
            ]
        )

    async def fetch_tickers(self) -> pl.DataFrame:
        data = await self._request("GET", f"{self.BASE_URL}/api/v3/ticker/24hr", weight=80)

        df = pl.DataFrame(data)

        return df.select(
            [
                pl.col("closeTime").cast(pl.Datetime("ms", "UTC")).alias("timestamp"),
                pl.lit(self.name).alias("exchange"),
                pl.col("symbol").alias(
                    "base"
                ),  # not strictly true but binance doesn't return base/quote directly here easily without exchange info
                pl.lit(None).cast(pl.String).alias("quote"),
                pl.col("lastPrice").cast(pl.Float64).alias("last_price"),
                pl.col("bidPrice").cast(pl.Float64).alias("bid_price"),
                pl.col("askPrice").cast(pl.Float64).alias("ask_price"),
                pl.col("highPrice").cast(pl.Float64).alias("high_24h"),
                pl.col("lowPrice").cast(pl.Float64).alias("low_24h"),
                pl.col("volume").cast(pl.Float64).alias("volume_24h_base"),
                pl.col("quoteVolume").cast(pl.Float64).alias("volume_24h_quote"),
                pl.col("priceChangePercent").cast(pl.Float64).alias("price_change_pct"),
            ]
        )
