"""OKX API v5 public market data adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, ClassVar

import polars as pl

from .base import BaseSource


class OKXSource(BaseSource):
    """OKX API v5 public market data source adapter.

    Handles OKX-specific idiosyncrasies:
    - Hyphenated instrument identifiers (e.g. BTC-USDT)
    - Uppercase bar intervals (1m, 1H, 4H, 1D)
    - Descending candle timestamps (re-sorted ascending to canonical order)
    - String-encoded prices and millisecond Unix timestamps
    """

    name = "okx"
    BASE_URL = "https://www.okx.com"

    # Interval mapping for OKX bar parameter
    INTERVAL_MAP: ClassVar[dict[str, str]] = {
        "1m": "1m",
        "3m": "3m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1H",
        "2h": "2H",
        "4h": "4H",
        "1d": "1D",
        "1w": "1W",
    }

    def normalise_symbol(self, base: str, quote: str) -> str:
        """Convert canonical (base, quote) pair to OKX instId (e.g. BTC-USDT)."""
        return f"{base.upper()}-{quote.upper()}"

    def _get_bar(self, interval: str) -> str:
        return self.INTERVAL_MAP.get(interval, "1H")

    async def fetch_ohlcv(
        self,
        base: str,
        quote: str,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> pl.DataFrame:
        inst_id = self.normalise_symbol(base, quote)
        bar = self._get_bar(interval)

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
            "instId": inst_id,
            "bar": bar,
            "before": start_ts,
            "after": end_ts,
            "limit": 100,
        }

        res = await self._request("GET", f"{self.BASE_URL}/api/v5/market/candles", params=params)

        if not res or not isinstance(res, dict) or "data" not in res:
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

        data = res.get("data", [])
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

        # OKX schema: [ts, open, high, low, close, vol, volCcy, volCcyQuote, confirm]
        df = pl.DataFrame(
            data,
            schema=[
                "ts",
                "open",
                "high",
                "low",
                "close",
                "vol",
                "vol_ccy",
                "vol_quote",
                "confirm",
            ],
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
                    pl.col("vol").cast(pl.Float64).alias("volume_base"),
                    pl.col("vol_ccy").cast(pl.Float64).alias("volume_quote"),
                    pl.lit(None).cast(pl.Int64).alias("trade_count"),
                    (pl.col("vol_ccy").cast(pl.Float64) / pl.col("vol").cast(pl.Float64)).alias(
                        "vwap"
                    ),
                    pl.lit(None).cast(pl.Float64).alias("taker_buy_volume"),
                ]
            )
            .sort("timestamp")
        )

    async def fetch_trades(self, base: str, quote: str, limit: int = 500) -> pl.DataFrame:
        inst_id = self.normalise_symbol(base, quote)
        params = {"instId": inst_id, "limit": min(limit, 100)}
        res = await self._request("GET", f"{self.BASE_URL}/api/v5/market/trades", params=params)

        data = res.get("data", []) if isinstance(res, dict) else []
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
                pl.col("ts").cast(pl.Int64).cast(pl.Datetime("ms", "UTC")).alias("timestamp"),
                pl.lit(self.name).alias("exchange"),
                pl.lit(base).alias("base"),
                pl.lit(quote).alias("quote"),
                pl.col("tradeId").cast(pl.String).alias("trade_id"),
                pl.col("px").cast(pl.Float64).alias("price"),
                pl.col("sz").cast(pl.Float64).alias("quantity"),
                pl.col("side").str.to_lowercase().alias("side"),
                pl.lit(None).cast(pl.Boolean).alias("is_maker"),
            ]
        ).sort("timestamp")

    async def fetch_ticker(self, base: str, quote: str) -> pl.DataFrame:
        inst_id = self.normalise_symbol(base, quote)
        params = {"instId": inst_id}
        res = await self._request("GET", f"{self.BASE_URL}/api/v5/market/ticker", params=params)

        data = res.get("data", []) if isinstance(res, dict) else []
        if not data:
            raise ValueError(f"No ticker returned for {inst_id} on OKX")

        item = data[0]
        last_px = float(item["last"])
        open_px = float(item.get("open24h", last_px))
        price_change_pct = ((last_px - open_px) / open_px * 100.0) if open_px > 0 else 0.0

        row = {
            "ts": int(item["ts"]),
            "last_price": last_px,
            "bid_price": float(item["bidPx"]),
            "ask_price": float(item["askPx"]),
            "high_24h": float(item["high24h"]),
            "low_24h": float(item["low24h"]),
            "volume_24h_base": float(item["vol24h"]),
            "volume_24h_quote": float(item["volCcy24h"]),
            "price_change_pct": price_change_pct,
        }

        df = pl.DataFrame([row])
        return df.select(
            [
                pl.col("ts").cast(pl.Datetime("ms", "UTC")).alias("timestamp"),
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
            "GET", f"{self.BASE_URL}/api/v5/market/tickers", params={"instType": "SPOT"}
        )
        data = res.get("data", []) if isinstance(res, dict) else []
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

        df = pl.DataFrame(data)
        # Parse instId into base and quote
        return df.with_columns(
            [
                pl.col("instId").str.split("-").list.get(0).alias("base"),
                pl.col("instId").str.split("-").list.get(1).alias("quote"),
                (
                    (
                        pl.col("last").cast(pl.Float64, strict=False)
                        - pl.col("open24h").cast(pl.Float64, strict=False)
                    )
                    / pl.col("open24h").cast(pl.Float64, strict=False)
                    * 100.0
                ).alias("price_change_pct"),
            ]
        ).select(
            [
                pl.col("ts").cast(pl.Int64).cast(pl.Datetime("ms", "UTC")).alias("timestamp"),
                pl.lit(self.name).alias("exchange"),
                pl.col("base"),
                pl.col("quote"),
                pl.col("last").cast(pl.Float64, strict=False).alias("last_price"),
                pl.col("bidPx").cast(pl.Float64, strict=False).alias("bid_price"),
                pl.col("askPx").cast(pl.Float64, strict=False).alias("ask_price"),
                pl.col("high24h").cast(pl.Float64, strict=False),
                pl.col("low24h").cast(pl.Float64, strict=False),
                pl.col("vol24h").cast(pl.Float64, strict=False).alias("volume_24h_base"),
                pl.col("volCcy24h").cast(pl.Float64, strict=False).alias("volume_24h_quote"),
                pl.col("price_change_pct").cast(pl.Float64, strict=False),
            ]
        )
