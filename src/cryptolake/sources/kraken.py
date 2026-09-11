"""Kraken public API market data adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, ClassVar

import polars as pl

from .base import BaseSource


class KrakenSource(BaseSource):
    """Kraken public market data source adapter.

    Handles Kraken-specific idiosyncrasies:
    - Legacy 4-letter asset prefixes (XXBT, XETH, ZUSD, ZEUR)
    - Dynamic dictionary keys in response payloads
    - Unix second timestamps mapped to canonical ``datetime[ms, UTC]``
    - Native trades schema with 'b'/'s' taker side indicators
    """

    name = "kraken"
    BASE_URL = "https://api.kraken.com/0/public"

    # Interval string to minutes
    INTERVAL_MAP: ClassVar[dict[str, int]] = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "4h": 240,
        "1d": 1440,
    }

    # Base asset translation for query parameters
    BASE_MAP: ClassVar[dict[str, str]] = {
        "BTC": "XBT",
        "DOGE": "XDG",
    }

    def normalise_symbol(self, base: str, quote: str) -> str:
        """Convert canonical (base, quote) to Kraken query pair (e.g. XBTUSD, ETHUSDT)."""
        kraken_base = self.BASE_MAP.get(base.upper(), base.upper())
        return f"{kraken_base}{quote.upper()}"

    def _get_interval_minutes(self, interval: str) -> int:
        return self.INTERVAL_MAP.get(interval, 60)

    async def fetch_ohlcv(
        self,
        base: str,
        quote: str,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> pl.DataFrame:
        pair = self.normalise_symbol(base, quote)
        interval_min = self._get_interval_minutes(interval)

        start_s = int(
            start.replace(tzinfo=timezone.utc).timestamp()
            if start.tzinfo is None
            else start.timestamp()
        )
        end_s = int(
            end.replace(tzinfo=timezone.utc).timestamp() if end.tzinfo is None else end.timestamp()
        )

        params: dict[str, Any] = {
            "pair": pair,
            "interval": interval_min,
            "since": start_s,
        }

        res = await self._request("GET", f"{self.BASE_URL}/OHLC", params=params)

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

        # In Kraken result, keys are e.g. "XXBTZUSD" and "last"
        result_dict: dict[str, Any] = res["result"]
        candle_data: list[Any] = []
        for k, v in result_dict.items():
            if k != "last" and isinstance(v, list):
                candle_data = v
                break

        if not candle_data:
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

        # Kraken columns: [time, open, high, low, close, vwap, volume, count]
        df = pl.DataFrame(
            candle_data,
            schema=["time_s", "open", "high", "low", "close", "vwap", "volume", "count"],
            orient="row",
        )

        return (
            df.filter(
                (pl.col("time_s").cast(pl.Int64) >= start_s)
                & (pl.col("time_s").cast(pl.Int64) <= end_s)
            )
            .select(
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
                    (pl.col("volume").cast(pl.Float64) * pl.col("vwap").cast(pl.Float64)).alias(
                        "volume_quote"
                    ),
                    pl.col("count").cast(pl.Int64).alias("trade_count"),
                    pl.col("vwap").cast(pl.Float64),
                    pl.lit(None).cast(pl.Float64).alias("taker_buy_volume"),
                ]
            )
            .sort("timestamp")
        )

    async def fetch_trades(self, base: str, quote: str, limit: int = 500) -> pl.DataFrame:
        pair = self.normalise_symbol(base, quote)
        res = await self._request("GET", f"{self.BASE_URL}/Trades", params={"pair": pair})

        if not res or not isinstance(res, dict) or "result" not in res:
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

        trades_list: list[Any] = []
        for k, v in res["result"].items():
            if k != "last" and isinstance(v, list):
                trades_list = v
                break

        if not trades_list:
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

        # Kraken trade array: [price, volume, time_float_s, buy_sell, market_limit, misc, trade_id]
        sliced = trades_list[:limit]
        rows = []
        for item in sliced:
            rows.append(
                {
                    "price": float(item[0]),
                    "quantity": float(item[1]),
                    "time_ms": int(float(item[2]) * 1000),
                    "side": "buy" if item[3] == "b" else "sell",
                    "trade_id": str(item[6]) if len(item) > 6 else str(item[2]),
                }
            )

        df = pl.DataFrame(rows)
        return df.select(
            [
                pl.col("time_ms").cast(pl.Datetime("ms", "UTC")).alias("timestamp"),
                pl.lit(self.name).alias("exchange"),
                pl.lit(base).alias("base"),
                pl.lit(quote).alias("quote"),
                pl.col("trade_id").cast(pl.String),
                pl.col("price").cast(pl.Float64),
                pl.col("quantity").cast(pl.Float64),
                pl.col("side").alias("side"),
                pl.lit(None).cast(pl.Boolean).alias("is_maker"),
            ]
        ).sort("timestamp")

    async def fetch_ticker(self, base: str, quote: str) -> pl.DataFrame:
        pair = self.normalise_symbol(base, quote)
        res = await self._request("GET", f"{self.BASE_URL}/Ticker", params={"pair": pair})

        if not res or not isinstance(res, dict) or "result" not in res:
            raise ValueError(f"No ticker returned for {pair} on Kraken")

        ticker_dict = {}
        for v in res["result"].values():
            if isinstance(v, dict):
                ticker_dict = v
                break

        if not ticker_dict:
            raise ValueError(f"Empty ticker object for {pair} on Kraken")

        last_px = float(ticker_dict["c"][0])
        bid_px = float(ticker_dict["b"][0])
        ask_px = float(ticker_dict["a"][0])
        high_px = float(ticker_dict["h"][1])
        low_px = float(ticker_dict["l"][1])
        vol_base = float(ticker_dict["v"][1])
        open_px = float(ticker_dict["o"])
        price_change_pct = ((last_px - open_px) / open_px * 100.0) if open_px > 0 else 0.0

        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

        df = pl.DataFrame(
            [
                {
                    "timestamp_ms": now_ms,
                    "last_price": last_px,
                    "bid_price": bid_px,
                    "ask_price": ask_px,
                    "high_24h": high_px,
                    "low_24h": low_px,
                    "volume_24h_base": vol_base,
                    "volume_24h_quote": vol_base * last_px,
                    "price_change_pct": price_change_pct,
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
