from __future__ import annotations

import polars as pl

KNOWN_QUOTE_CURRENCIES = {
    "USDT",
    "USD",
    "USDC",
    "EUR",
    "GBP",
    "BTC",
    "ETH",
    "BNB",
    "BUSD",
    "DAI",
    "TUSD",
}

KRAKEN_SYMBOL_MAP = {
    "XXBT": "BTC",
    "XETH": "ETH",
    "XXRP": "XRP",
    "XLTC": "LTC",
    "ZUSD": "USD",
    "ZEUR": "EUR",
    "ZGBP": "GBP",
    "ZCAD": "CAD",
    "ZJPY": "JPY",
}


def normalise_timestamp(col: pl.Expr, unit: str) -> pl.Expr:
    """Convert timestamps to Datetime('ms', 'UTC')."""
    if unit == "ms":
        return col.cast(pl.Int64).cast(pl.Datetime("ms", "UTC"))
    elif unit == "s":
        return (col.cast(pl.Float64) * 1000).cast(pl.Int64).cast(pl.Datetime("ms", "UTC"))
    elif unit == "ns":
        return (col.cast(pl.Int64) // 1000000).cast(pl.Datetime("ms", "UTC"))
    elif unit == "iso8601":
        return col.str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M:%S%.f%Z", strict=False).cast(
            pl.Datetime("ms", "UTC")
        )
    else:
        raise ValueError(f"Unknown timestamp unit: {unit}")


def normalise_side(col: pl.Expr, mapping: dict[str, str]) -> pl.Expr:
    """Map exchange-specific side values to canonical 'buy'/'sell'."""
    return col.replace(mapping, default=col)


def normalise_symbol_pair(raw_symbol: str, exchange: str) -> tuple[str, str]:
    """Parse exchange-native symbols into (base, quote) tuples."""
    raw_symbol = raw_symbol.upper()
    exchange_lower = exchange.lower()

    if exchange_lower == "kraken":
        if raw_symbol.endswith("USDT"):
            base = raw_symbol[:-4]
            quote = "USDT"
        elif len(raw_symbol) >= 7 and raw_symbol.startswith(("X", "Z")):
            base_raw = raw_symbol[:-4]
            quote_raw = raw_symbol[-4:]
            base = KRAKEN_SYMBOL_MAP.get(
                base_raw, base_raw[1:] if base_raw.startswith(("X", "Z")) else base_raw
            )
            quote = KRAKEN_SYMBOL_MAP.get(
                quote_raw, quote_raw[1:] if quote_raw.startswith(("X", "Z")) else quote_raw
            )
        else:
            # Fallback for simple kraken pairs like BTCUSD
            base_raw, quote_raw = raw_symbol[:-3], raw_symbol[-3:]
            if raw_symbol.endswith("USDT"):
                base_raw, quote_raw = raw_symbol[:-4], raw_symbol[-4:]
            base = KRAKEN_SYMBOL_MAP.get(base_raw, base_raw)
            quote = KRAKEN_SYMBOL_MAP.get(quote_raw, quote_raw)

        return base, quote

    elif exchange_lower in ("coinbase", "okx"):
        parts = raw_symbol.split("-")
        if len(parts) >= 2:
            return parts[0], parts[1]

    # Default matching for Binance, Bybit, etc.
    # Greedily match longest known quote currency first
    for qc in sorted(KNOWN_QUOTE_CURRENCIES, key=len, reverse=True):
        if raw_symbol.endswith(qc):
            base = raw_symbol[: -len(qc)]
            if base:
                return base, qc

    return raw_symbol, ""
