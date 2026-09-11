"""Coinbase Exchange API market data adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, ClassVar

import polars as pl

from .base import BaseSource


class CoinbaseSource(BaseSource):
    """Coinbase Exchange public market data source adapter.

    Handles Coinbase-specific idiosyncrasies:
    - LHOCV candle ordering: ``[time, low, high, open, close, volume]``
    - Descending candle timestamps (re-sorted ascending to canonical order)
    - Unix second timestamps mapped to canonical ``datetime[ms, UTC]``
    """

    name = "coinbase"
    BASE_URL = "https://api.exchange.coinbase.com"

    # Supported granularities in seconds
    GRANULARITY_MAP: ClassVar[dict[str, int]] = {
        "1m": 60,
        "5m": 300,
        "15m": 900,
        "1h": 3600,
        "6h": 21600,
        "1d": 86400,
    }

    def _headers(self) -> dict[str, str]:
        return {"User-Agent": "CryptoLake/0.1.0"}

    def normalise_symbol(self, base: str, quote: str) -> str:
        """Convert canonical (base, quote) pair to Coinbase product ID (e.g. BTC-USD)."""
        return f"{base.upper()}-{quote.upper()}"

    def _get_granularity(self, interval: str) -> int:
        return self.GRANULARITY_MAP.get(interval, 3600)

    async def fetch_ohlcv(
        self,
        base: str,
        quote: str,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> pl.DataFrame:
        product_id = self.normalise_symbol(base, quote)
        granularity = self._get_granularity(interval)

        start_iso = (
            start.replace(tzinfo=timezone.utc).isoformat()
            if start.tzinfo is None
            else start.isoformat()
        )
        end_iso = (
            end.replace(tzinfo=timezone.utc).isoformat() if end.tzinfo is None else end.isoformat()
        )

        params: dict[str, Any] = {
            "granularity": granularity,
            "start": start_iso,
            "end": end_iso,
        }

        data = await self._request(
            "GET",
            f"{self.BASE_URL}/products/{product_id}/candles",
            params=params,
            headers=self._headers(),
        )

        if not data:
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

        # Coinbase returns [time, low, high, open, close, volume] (LHOCV order)
        df = pl.DataFrame(
            data,
            schema=["time_s", "low", "high", "open", "close", "volume"],
            orient="row",
        )

        return df.select(
            [
                (pl.col("time_s").cast(pl.Int64) * 1000)
                .cast(pl.Datetime("ms", "UTC"))
                .alias("timestamp"),
                pl.lit(self.name).alias("exchange"),
                pl.lit(base).alias("base"),
                pl.lit(quote).alias("quote"),
                pl.lit(interval).alias("interval"),
                pl.col("open").cast(pl.Float64),
                pl.col("high").cast(pl.Float64),
                pl.col("low").cast(pl.Float64),
                pl.col("close").cast(pl.Float64),
                pl.col("volume").cast(pl.Float64).alias("volume_base"),
                (pl.col("volume").cast(pl.Float64) * pl.col("close").cast(pl.Float64)).alias(
                    "volume_quote"
                ),
                pl.lit(None).cast(pl.Int64).alias("trade_count"),
                pl.lit(None).cast(pl.Float64).alias("vwap"),
                pl.lit(None).cast(pl.Float64).alias("taker_buy_volume"),
            ]
        ).sort("timestamp")

    async def fetch_trades(self, base: str, quote: str, limit: int = 500) -> pl.DataFrame:
        product_id = self.normalise_symbol(base, quote)
        data = await self._request(
            "GET",
            f"{self.BASE_URL}/products/{product_id}/trades",
            headers=self._headers(),
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

        df = pl.DataFrame(data[:limit])
        return df.select(
            [
                pl.col("time")
                .str.strptime(pl.Datetime("ms"), "%Y-%m-%dT%H:%M:%S%.fZ", strict=False)
                .cast(pl.Datetime("ms", "UTC"))
                .alias("timestamp"),
                pl.lit(self.name).alias("exchange"),
                pl.lit(base).alias("base"),
                pl.lit(quote).alias("quote"),
                pl.col("trade_id").cast(pl.String),
                pl.col("price").cast(pl.Float64),
                pl.col("size").cast(pl.Float64).alias("quantity"),
                pl.col("side").str.to_lowercase().alias("side"),
                pl.lit(None).cast(pl.Boolean).alias("is_maker"),
            ]
        ).sort("timestamp")

    async def fetch_ticker(self, base: str, quote: str) -> pl.DataFrame:
        product_id = self.normalise_symbol(base, quote)
        ticker_data = await self._request(
            "GET",
            f"{self.BASE_URL}/products/{product_id}/ticker",
            headers=self._headers(),
        )
        stats_data = await self._request(
            "GET",
            f"{self.BASE_URL}/products/{product_id}/stats",
            headers=self._headers(),
        )

        ts_str = ticker_data.get("time")
        last_px = float(ticker_data.get("price", 0.0))
        open_px = float(stats_data.get("open", last_px)) if stats_data else last_px
        price_change_pct = ((last_px - open_px) / open_px * 100.0) if open_px > 0 else 0.0

        row = {
            "time": ts_str,
            "last_price": last_px,
            "bid_price": float(ticker_data.get("bid", 0.0)),
            "ask_price": float(ticker_data.get("ask", 0.0)),
            "high_24h": float(stats_data.get("high", 0.0)) if stats_data else last_px,
            "low_24h": float(stats_data.get("low", 0.0)) if stats_data else last_px,
            "volume_24h_base": float(ticker_data.get("volume", 0.0)),
            "volume_24h_quote": float(ticker_data.get("volume", 0.0)) * last_px,
            "price_change_pct": price_change_pct,
        }

        df = pl.DataFrame([row])
        return df.select(
            [
                pl.col("time")
                .str.strptime(pl.Datetime("ms"), "%Y-%m-%dT%H:%M:%S%.fZ", strict=False)
                .cast(pl.Datetime("ms", "UTC"))
                .alias("timestamp"),
                pl.lit(self.name).alias("exchange"),
                pl.lit(base).alias("base"),
                pl.lit(quote).alias("quote"),
                pl.col("last_price").cast(pl.Float64),
                pl.col("bid_price").cast(pl.Float64),
                pl.col("ask_price").cast(pl.Float64),
                pl.col("high_24h").cast(pl.Float64),
                pl.col("low_24h").cast(pl.Float64),
                pl.col("volume_24h_base").cast(pl.Float64),
                pl.col("volume_24h_quote").cast(pl.Float64),
                pl.col("price_change_pct").cast(pl.Float64),
            ]
        )

    async def fetch_tickers(self) -> pl.DataFrame:
        """Fetch tickers for standard tracked products on Coinbase."""
        tracked = [("BTC", "USD"), ("ETH", "USD"), ("SOL", "USD"), ("BTC", "USDT"), ("ETH", "USDT")]
        dfs: list[pl.DataFrame] = []
        for base, quote in tracked:
            try:
                t_df = await self.fetch_ticker(base, quote)
                if not t_df.is_empty():
                    dfs.append(t_df)
            except Exception:
                continue

        if not dfs:
            return pl.DataFrame(
                schema={
                    "timestamp": pl.Datetime("ms", "UTC"),
                    "exchange": pl.String,
                    "base": pl.String,
                    "quote": pl.String,
                    "last_price": pl.Float64,
                    "bid_price": pl.Float64,
                    "ask_price": pl.Float64,
                    "high_24h": pl.Float64,
                    "low_24h": pl.Float64,
                    "volume_24h_base": pl.Float64,
                    "volume_24h_quote": pl.Float64,
                    "price_change_pct": pl.Float64,
                }
            )

        return pl.concat(dfs, how="vertical")
