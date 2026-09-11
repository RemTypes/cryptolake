"""CryptoCompare public API market data adapter."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import polars as pl

from .base import BaseSource


class CryptoCompareSource(BaseSource):
    """CryptoCompare public market data aggregator adapter.

    Provides historical granular OHLCV candles (minute, hour, day)
    and full multi-exchange aggregated ticker statistics.
    """

    name = "cryptocompare"
    BASE_URL = "https://min-api.cryptocompare.com/data"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.api_key = os.environ.get("CRYPTOCOMPARE_API_KEY")

    def _get_headers(self) -> dict[str, str]:
        headers = {}
        if self.api_key:
            headers["authorization"] = f"Apikey {self.api_key}"
        return headers

    def normalise_symbol(self, base: str, quote: str) -> str:
        return f"{base.upper()}/{quote.upper()}"

    def _get_endpoint_for_interval(self, interval: str) -> str:
        if interval in ("1m", "5m", "15m", "30m"):
            return "v2/histominute"
        elif interval in ("1h", "2h", "4h", "6h", "12h"):
            return "v2/histohour"
        else:
            return "v2/histoday"

    async def fetch_ohlcv(
        self,
        base: str,
        quote: str,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> pl.DataFrame:
        endpoint = self._get_endpoint_for_interval(interval)

        start_s = int(
            start.replace(tzinfo=timezone.utc).timestamp()
            if start.tzinfo is None
            else start.timestamp()
        )
        end_s = int(
            end.replace(tzinfo=timezone.utc).timestamp() if end.tzinfo is None else end.timestamp()
        )

        params: dict[str, Any] = {
            "fsym": base.upper(),
            "tsym": quote.upper(),
            "toTs": end_s,
            "limit": 2000,
        }

        res = await self._request(
            "GET",
            f"{self.BASE_URL}/{endpoint}",
            params=params,
            headers=self._get_headers(),
        )

        if not res or not isinstance(res, dict) or res.get("Response") != "Success":
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

        raw_list = res.get("Data", {}).get("Data", [])
        if not raw_list:
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

        df = pl.DataFrame(raw_list)

        return (
            df.filter(
                (pl.col("time").cast(pl.Int64) >= start_s)
                & (pl.col("time").cast(pl.Int64) <= end_s)
            )
            .select(
                [
                    (pl.col("time").cast(pl.Int64) * 1000)
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
                    pl.col("volumefrom").cast(pl.Float64).alias("volume_base"),
                    pl.col("volumeto").cast(pl.Float64).alias("volume_quote"),
                    pl.lit(None).cast(pl.Int64).alias("trade_count"),
                    (
                        pl.col("volumeto").cast(pl.Float64) / pl.col("volumefrom").cast(pl.Float64)
                    ).alias("vwap"),
                    pl.lit(None).cast(pl.Float64).alias("taker_buy_volume"),
                ]
            )
            .sort("timestamp")
        )

    async def fetch_trades(self, base: str, quote: str, limit: int = 500) -> pl.DataFrame:
        raise NotImplementedError("CryptoCompare free tier does not provide raw trade executions.")

    async def fetch_ticker(self, base: str, quote: str) -> pl.DataFrame:
        params = {"fsyms": base.upper(), "tsyms": quote.upper()}
        res = await self._request(
            "GET",
            f"{self.BASE_URL}/pricemultifull",
            params=params,
            headers=self._get_headers(),
        )

        raw = res.get("RAW", {}).get(base.upper(), {}).get(quote.upper(), {})
        if not raw:
            raise ValueError(f"No ticker found for {base}/{quote} on CryptoCompare")

        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        df = pl.DataFrame(
            [
                {
                    "timestamp_ms": now_ms,
                    "last_price": float(raw.get("PRICE", 0.0)),
                    "bid_price": float(raw.get("BID", 0.0)),
                    "ask_price": float(raw.get("ASK", 0.0)),
                    "high_24h": float(raw.get("HIGHDAY", 0.0)),
                    "low_24h": float(raw.get("LOWDAY", 0.0)),
                    "volume_24h_base": float(raw.get("VOLUME24HOUR", 0.0)),
                    "volume_24h_quote": float(raw.get("VOLUME24HOURTO", 0.0)),
                    "price_change_pct": float(raw.get("CHANGEPCT24HOUR", 0.0)),
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
