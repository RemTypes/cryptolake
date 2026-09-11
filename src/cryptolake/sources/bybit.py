"""Bybit v5 public market data adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, ClassVar

import polars as pl

from .base import BaseSource


class BybitSource(BaseSource):
    """Bybit v5 public market data source adapter.

    Handles Bybit-specific idiosyncrasies:
    - Numeric string intervals (e.g. "60" for 1h, "D" for 1d)
    - Descending candle timestamps (re-sorted ascending to canonical order)
    - Spot category parameter required on all market endpoints
    - Turnover mapped to volume_quote
    """

    name = "bybit"
    BASE_URL = "https://api.bybit.com"

    # Interval mapping for Bybit kline parameter
    INTERVAL_MAP: ClassVar[dict[str, str]] = {
        "1m": "1",
        "3m": "3",
        "5m": "5",
        "15m": "15",
        "30m": "30",
        "1h": "60",
        "2h": "120",
        "4h": "240",
        "6h": "360",
        "12h": "720",
        "1d": "D",
        "1w": "W",
    }

    def normalise_symbol(self, base: str, quote: str) -> str:
        """Convert canonical (base, quote) pair to Bybit symbol (e.g. BTCUSDT)."""
        return f"{base.upper()}{quote.upper()}"

    def _get_interval(self, interval: str) -> str:
        return self.INTERVAL_MAP.get(interval, "60")

    async def fetch_ohlcv(
        self,
        base: str,
        quote: str,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> pl.DataFrame:
        symbol = self.normalise_symbol(base, quote)
        bybit_interval = self._get_interval(interval)

        start_ts = int(
            start.replace(tzinfo=timezone.utc).timestamp() * 1000
            if start.tzinfo is None
            else start.timestamp() * 1000
        )
        end_ts = int(
            end.replace(tzinfo=timezone.utc).timestamp() * 1000
            if end.tzinfo is None
            else end.timestamp() * 1000
        )

        params: dict[str, Any] = {
            "category": "spot",
            "symbol": symbol,
            "interval": bybit_interval,
            "start": start_ts,
            "end": end_ts,
            "limit": 1000,
        }

        res = await self._request("GET", f"{self.BASE_URL}/v5/market/kline", params=params)

        if not res or not isinstance(res, dict) or "result" not in res:
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

        data = res.get("result", {}).get("list", [])
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

        # Bybit schema: [startTime, open, high, low, close, volume, turnover]
        df = pl.DataFrame(
            data,
            schema=["ts", "open", "high", "low", "close", "volume", "turnover"],
            orient="row",
        )

        return (
            df.filter(
                (pl.col("ts").cast(pl.Int64) >= start_ts) & (pl.col("ts").cast(pl.Int64) <= end_ts)
            )
            .select(
                [
                    pl.col("ts").cast(pl.Int64).cast(pl.Datetime("ms", "UTC")).alias("timestamp"),
                    pl.lit(self.name).alias("exchange"),
                    pl.lit(base).alias("base"),
                    pl.lit(quote).alias("quote"),
                    pl.lit(interval).alias("interval"),
                    pl.col("open").cast(pl.Float64),
                    pl.col("high").cast(pl.Float64),
                    pl.col("low").cast(pl.Float64),
                    pl.col("close").cast(pl.Float64),
                    pl.col("volume").cast(pl.Float64).alias("volume_base"),
                    pl.col("turnover").cast(pl.Float64).alias("volume_quote"),
                    pl.lit(None).cast(pl.Int64).alias("trade_count"),
                    (pl.col("turnover").cast(pl.Float64) / pl.col("volume").cast(pl.Float64)).alias(
                        "vwap"
                    ),
                    pl.lit(None).cast(pl.Float64).alias("taker_buy_volume"),
                ]
            )
            .sort("timestamp")
        )

    async def fetch_trades(self, base: str, quote: str, limit: int = 500) -> pl.DataFrame:
        symbol = self.normalise_symbol(base, quote)
        params = {"category": "spot", "symbol": symbol, "limit": min(limit, 60)}
        res = await self._request("GET", f"{self.BASE_URL}/v5/market/recent-trade", params=params)

        data = res.get("result", {}).get("list", []) if isinstance(res, dict) else []
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
                pl.col("time").cast(pl.Int64).cast(pl.Datetime("ms", "UTC")).alias("timestamp"),
                pl.lit(self.name).alias("exchange"),
                pl.lit(base).alias("base"),
                pl.lit(quote).alias("quote"),
                pl.col("execId").cast(pl.String).alias("trade_id"),
                pl.col("price").cast(pl.Float64),
                pl.col("size").cast(pl.Float64).alias("quantity"),
                pl.col("side").str.to_lowercase().alias("side"),
                pl.lit(None).cast(pl.Boolean).alias("is_maker"),
            ]
        ).sort("timestamp")

    async def fetch_ticker(self, base: str, quote: str) -> pl.DataFrame:
        symbol = self.normalise_symbol(base, quote)
        params = {"category": "spot", "symbol": symbol}
        res = await self._request("GET", f"{self.BASE_URL}/v5/market/tickers", params=params)

        data = res.get("result", {}).get("list", []) if isinstance(res, dict) else []
        if not data:
            raise ValueError(f"No ticker returned for {symbol} on Bybit")

        item = data[0]
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

        df = pl.DataFrame(
            [
                {
                    "timestamp_ms": now_ms,
                    "last_price": float(item["lastPrice"]),
                    "bid_price": float(item["bid1Price"]),
                    "ask_price": float(item["ask1Price"]),
                    "high_24h": float(item["highPrice24h"]),
                    "low_24h": float(item["lowPrice24h"]),
                    "volume_24h_base": float(item["volume24h"]),
                    "volume_24h_quote": float(item["turnover24h"]),
                    "price_change_pct": float(item["price24hPcnt"]) * 100.0,
                }
            ]
        )

        return df.select(
            [
                pl.col("timestamp_ms").cast(pl.Datetime("ms", "UTC")).alias("timestamp"),
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
        res = await self._request(
            "GET", f"{self.BASE_URL}/v5/market/tickers", params={"category": "spot"}
        )
        data = res.get("result", {}).get("list", []) if isinstance(res, dict) else []
        if not data:
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

        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        df = pl.DataFrame(data)

        return df.with_columns(
            [
                pl.lit(now_ms).cast(pl.Datetime("ms", "UTC")).alias("timestamp"),
                pl.lit(self.name).alias("exchange"),
                pl.col("symbol").alias("base"),
                pl.lit(None).cast(pl.String).alias("quote"),
                pl.col("lastPrice").cast(pl.Float64).alias("last_price"),
                pl.col("bid1Price").cast(pl.Float64).alias("bid_price"),
                pl.col("ask1Price").cast(pl.Float64).alias("ask_price"),
                pl.col("highPrice24h").cast(pl.Float64).alias("high_24h"),
                pl.col("lowPrice24h").cast(pl.Float64).alias("low_24h"),
                pl.col("volume24h").cast(pl.Float64).alias("volume_24h_base"),
                pl.col("turnover24h").cast(pl.Float64).alias("volume_24h_quote"),
                (pl.col("price24hPcnt").cast(pl.Float64) * 100.0).alias("price_change_pct"),
            ]
        ).select(
            [
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
        )
