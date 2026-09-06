"""CoinGecko API v3 data source adapter."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, ClassVar

import polars as pl

from .base import BaseSource


class CoinGeckoSource(BaseSource):
    name = "coingecko"
    BASE_URL = "https://api.coingecko.com/api/v3"

    # Top 20 hardcoded mapping
    SYMBOL_MAP: ClassVar[dict[str, str]] = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "USDT": "tether",
        "BNB": "binancecoin",
        "SOL": "solana",
        "USDC": "usd-coin",
        "XRP": "ripple",
        "ADA": "cardano",
        "AVAX": "avalanche-2",
        "DOGE": "dogecoin",
        "DOT": "polkadot",
        "TRX": "tron",
        "LINK": "chainlink",
        "MATIC": "matic-network",
        "TON": "the-open-network",
        "SHIB": "shiba-inu",
        "LTC": "litecoin",
        "BCH": "bitcoin-cash",
        "ATOM": "cosmos",
        "UNI": "uniswap",
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.api_key = os.environ.get("CG_API_KEY")

    def _get_headers(self) -> dict[str, str]:
        headers = {}
        if self.api_key:
            headers["x-cg-demo-api-key"] = self.api_key
        return headers

    async def _resolve_id(self, symbol: str) -> str:
        symbol = symbol.upper()
        if symbol in self.SYMBOL_MAP:
            return self.SYMBOL_MAP[symbol]

        data = await self._request(
            "GET", f"{self.BASE_URL}/search", params={"query": symbol}, headers=self._get_headers()
        )
        coins = data.get("coins", [])
        for coin in coins:
            if coin["symbol"].upper() == symbol:
                return str(coin["id"])

        raise ValueError(f"Could not resolve CoinGecko ID for {symbol}")

    def normalise_symbol(self, base: str, quote: str) -> str:
        return f"{base.lower()}_{quote.lower()}"

    async def fetch_ohlcv(
        self,
        base: str,
        quote: str,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> pl.DataFrame:
        cg_id = await self._resolve_id(base)

        # calculate days based on start and end
        delta = end - start
        days = max(1, delta.days)

        if days <= 1:
            days_str = "1"
        elif days <= 7:
            days_str = "7"
        elif days <= 14:
            days_str = "14"
        elif days <= 30:
            days_str = "30"
        elif days <= 90:
            days_str = "90"
        elif days <= 365:
            days_str = "365"
        else:
            days_str = "max"

        headers = self._get_headers()

        # fetch OHLC
        ohlc_params = {"vs_currency": quote.lower(), "days": days_str}
        ohlc_data = await self._request(
            "GET", f"{self.BASE_URL}/coins/{cg_id}/ohlc", params=ohlc_params, headers=headers
        )

        # fetch volumes
        market_params = {"vs_currency": quote.lower(), "days": days_str}
        market_data = await self._request(
            "GET",
            f"{self.BASE_URL}/coins/{cg_id}/market_chart",
            params=market_params,
            headers=headers,
        )

        if not ohlc_data:
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

        df_ohlc = pl.DataFrame(
            ohlc_data, schema=["timestamp_ms", "open", "high", "low", "close"], orient="row"
        )
        df_vol = pl.DataFrame(
            market_data.get("total_volumes", []),
            schema=["timestamp_ms", "volume_quote"],
            orient="row",
        )

        # join on timestamp (approximate since they might not align perfectly, but using as-of join)
        df_ohlc = df_ohlc.with_columns(pl.col("timestamp_ms").cast(pl.Int64))
        df_vol = df_vol.with_columns(pl.col("timestamp_ms").cast(pl.Int64))

        df_ohlc = df_ohlc.sort("timestamp_ms")
        df_vol = df_vol.sort("timestamp_ms")

        df = df_ohlc.join_asof(df_vol, on="timestamp_ms", strategy="nearest")

        # filter to the start/end range
        start_ts = int(start.replace(tzinfo=timezone.utc).timestamp() * 1000)
        end_ts = int(end.replace(tzinfo=timezone.utc).timestamp() * 1000)
        df = df.filter((pl.col("timestamp_ms") >= start_ts) & (pl.col("timestamp_ms") <= end_ts))

        return df.select(
            [
                pl.col("timestamp_ms").cast(pl.Datetime("ms", "UTC")).alias("timestamp"),
                pl.lit(self.name).alias("exchange"),
                pl.lit(base).alias("base"),
                pl.lit(quote).alias("quote"),
                pl.lit(interval).alias("interval"),
                pl.col("open").cast(pl.Float64),
                pl.col("high").cast(pl.Float64),
                pl.col("low").cast(pl.Float64),
                pl.col("close").cast(pl.Float64),
                (pl.col("volume_quote").cast(pl.Float64) / pl.col("close").cast(pl.Float64)).alias(
                    "volume_base"
                ),
                pl.col("volume_quote").cast(pl.Float64),
                pl.lit(None).cast(pl.Int64).alias("trade_count"),
                pl.lit(None).cast(pl.Float64).alias("vwap"),
                pl.lit(None).cast(pl.Float64).alias("taker_buy_volume"),
            ]
        )

    async def fetch_trades(self, base: str, quote: str, limit: int = 500) -> pl.DataFrame:
        raise NotImplementedError("CoinGecko does not support fetching trades.")

    async def fetch_ticker(self, base: str, quote: str) -> pl.DataFrame:
        cg_id = await self._resolve_id(base)
        quote_lower = quote.lower()

        params = {
            "ids": cg_id,
            "vs_currencies": quote_lower,
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
            "include_last_updated_at": "true",
        }

        data = await self._request(
            "GET", f"{self.BASE_URL}/simple/price", params=params, headers=self._get_headers()
        )

        if cg_id not in data:
            raise ValueError(f"No data returned for {cg_id}")

        ticker = data[cg_id]

        ts = ticker.get("last_updated_at")

        df = pl.DataFrame(
            [
                {
                    "timestamp_s": ts,
                    "last_price": ticker.get(quote_lower),
                    "volume_24h_quote": ticker.get(f"{quote_lower}_24h_vol"),
                    "price_change_pct": ticker.get(f"{quote_lower}_24h_change"),
                }
            ]
        )

        return df.select(
            [
                (pl.col("timestamp_s") * 1000).cast(pl.Datetime("ms", "UTC")).alias("timestamp"),
                pl.lit(self.name).alias("exchange"),
                pl.lit(base).alias("base"),
                pl.lit(quote).alias("quote"),
                pl.col("last_price").cast(pl.Float64),
                pl.lit(None).cast(pl.Float64).alias("bid_price"),
                pl.lit(None).cast(pl.Float64).alias("ask_price"),
                pl.lit(None).cast(pl.Float64).alias("high_24h"),
                pl.lit(None).cast(pl.Float64).alias("low_24h"),
                (
                    pl.col("volume_24h_quote").cast(pl.Float64)
                    / pl.col("last_price").cast(pl.Float64)
                ).alias("volume_24h_base"),
                pl.col("volume_24h_quote").cast(pl.Float64),
                pl.col("price_change_pct").cast(pl.Float64),
            ]
        )

    async def fetch_tickers(self) -> pl.DataFrame:
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 100,
            "page": 1,
        }

        data = await self._request(
            "GET", f"{self.BASE_URL}/coins/markets", params=params, headers=self._get_headers()
        )

        df = pl.DataFrame(data)

        return df.select(
            [
                pl.col("last_updated")
                .str.strptime(pl.Datetime("ms"), "%Y-%m-%dT%H:%M:%S.%fZ")
                .cast(pl.Datetime("ms", "UTC"))
                .alias("timestamp"),
                pl.lit(self.name).alias("exchange"),
                pl.col("symbol").str.to_uppercase().alias("base"),
                pl.lit("USD").alias("quote"),
                pl.col("current_price").cast(pl.Float64).alias("last_price"),
                pl.lit(None).cast(pl.Float64).alias("bid_price"),
                pl.lit(None).cast(pl.Float64).alias("ask_price"),
                pl.col("high_24h").cast(pl.Float64),
                pl.col("low_24h").cast(pl.Float64),
                (
                    pl.col("total_volume").cast(pl.Float64)
                    / pl.col("current_price").cast(pl.Float64)
                ).alias("volume_24h_base"),
                pl.col("total_volume").cast(pl.Float64).alias("volume_24h_quote"),
                pl.col("price_change_percentage_24h").cast(pl.Float64).alias("price_change_pct"),
            ]
        )
