from __future__ import annotations

from datetime import datetime
from pathlib import Path

import polars as pl
import structlog

from cryptolake.schemas.ohlcv import OHLCV_SCHEMA
from cryptolake.schemas.ticker import TICKER_SCHEMA
from cryptolake.schemas.trades import TRADE_SCHEMA

logger = structlog.get_logger()


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_partitioned(
    df: pl.DataFrame,
    data_dir: Path,
    dataset_name: str,
    partition_cols: list[str],
    date_col: str,
    unique_cols: list[str],
) -> Path:
    """Generic helper to write partitioned data and deduplicate."""
    out_dir = data_dir / dataset_name
    _ensure_dir(out_dir)

    # Ensure date column exists for partitioning
    if "date" not in df.columns:
        df = df.with_columns(pl.col(date_col).dt.date().cast(pl.Utf8).alias("date"))

    partitions = df.partition_by([*partition_cols, "date"], as_dict=True)

    for part_keys, part_df in partitions.items():
        # part_keys is a tuple of the partition values
        # Build the subpath
        rel_path = Path()
        for i, col in enumerate(partition_cols):
            # Special case: base-quote
            if col == "base" and i + 1 < len(partition_cols) and partition_cols[i + 1] == "quote":
                continue
            if col == "quote" and i > 0 and partition_cols[i - 1] == "base":
                base_val = part_keys[i - 1]
                quote_val = part_keys[i]
                rel_path = rel_path / f"{base_val}-{quote_val}"
            else:
                rel_path = rel_path / str(part_keys[i])

        date_str = str(part_keys[-1])
        target_dir = out_dir / rel_path
        _ensure_dir(target_dir)

        target_file = target_dir / f"{date_str}.parquet"

        final_df = part_df.drop("date")

        if target_file.exists():
            existing_df = pl.read_parquet(target_file)
            final_df = pl.concat([existing_df, final_df], how="vertical")
            final_df = final_df.unique(subset=unique_cols, keep="last")

        final_df.write_parquet(target_file, compression="snappy", use_pyarrow=True)

    return out_dir


def write_ohlcv(df: pl.DataFrame, data_dir: Path) -> Path:
    """Write OHLCV data partitioned as {data_dir}/ohlcv/{exchange}/{BASE}-{QUOTE}/{interval}/{YYYY-MM-DD}.parquet"""
    return _write_partitioned(
        df,
        data_dir,
        "ohlcv",
        ["exchange", "base", "quote", "interval"],
        "timestamp",
        ["timestamp", "exchange", "base", "quote", "interval"],
    )


def write_trades(df: pl.DataFrame, data_dir: Path) -> Path:
    """Write trades partitioned as {data_dir}/trades/{exchange}/{BASE}-{QUOTE}/{YYYY-MM-DD}.parquet"""
    return _write_partitioned(
        df,
        data_dir,
        "trades",
        ["exchange", "base", "quote"],
        "timestamp",
        ["timestamp", "exchange", "base", "quote", "trade_id"],
    )


def write_tickers(df: pl.DataFrame, data_dir: Path) -> Path:
    """Write tickers as {data_dir}/tickers/{exchange}/{YYYY-MM-DD}.parquet"""
    return _write_partitioned(
        df,
        data_dir,
        "tickers",
        ["exchange"],
        "timestamp",
        ["timestamp", "exchange", "base", "quote"],
    )


def read_ohlcv(
    data_dir: Path,
    exchange: str | None = None,
    base: str | None = None,
    quote: str | None = None,
    interval: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> pl.LazyFrame:
    """Read OHLCV data with predicate pushdown."""
    target_dir = data_dir / "ohlcv"
    if not target_dir.exists() or not any(target_dir.glob("**/*.parquet")):
        return pl.DataFrame(schema=OHLCV_SCHEMA).lazy()

    pattern = f"{data_dir}/ohlcv/**/*.parquet"
    lf = pl.scan_parquet(pattern)

    if exchange:
        lf = lf.filter(pl.col("exchange") == exchange)
    if base:
        lf = lf.filter(pl.col("base") == base)
    if quote:
        lf = lf.filter(pl.col("quote") == quote)
    if interval:
        lf = lf.filter(pl.col("interval") == interval)
    if start:
        lf = lf.filter(pl.col("timestamp") >= pl.lit(start))
    if end:
        lf = lf.filter(pl.col("timestamp") <= pl.lit(end))

    return lf


def read_trades(
    data_dir: Path,
    exchange: str | None = None,
    base: str | None = None,
    quote: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> pl.LazyFrame:
    """Read trades data with predicate pushdown."""
    target_dir = data_dir / "trades"
    if not target_dir.exists() or not any(target_dir.glob("**/*.parquet")):
        return pl.DataFrame(schema=TRADE_SCHEMA).lazy()

    pattern = f"{data_dir}/trades/**/*.parquet"
    lf = pl.scan_parquet(pattern)

    if exchange:
        lf = lf.filter(pl.col("exchange") == exchange)
    if base:
        lf = lf.filter(pl.col("base") == base)
    if quote:
        lf = lf.filter(pl.col("quote") == quote)
    if start:
        lf = lf.filter(pl.col("timestamp") >= pl.lit(start))
    if end:
        lf = lf.filter(pl.col("timestamp") <= pl.lit(end))

    return lf


def read_tickers(
    data_dir: Path,
    exchange: str | None = None,
    base: str | None = None,
    quote: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> pl.LazyFrame:
    """Read tickers data with predicate pushdown."""
    target_dir = data_dir / "tickers"
    if not target_dir.exists() or not any(target_dir.glob("**/*.parquet")):
        return pl.DataFrame(schema=TICKER_SCHEMA).lazy()

    pattern = f"{data_dir}/tickers/**/*.parquet"
    lf = pl.scan_parquet(pattern)

    if exchange:
        lf = lf.filter(pl.col("exchange") == exchange)
    if base:
        lf = lf.filter(pl.col("base") == base)
    if quote:
        lf = lf.filter(pl.col("quote") == quote)
    if start:
        lf = lf.filter(pl.col("timestamp") >= pl.lit(start))
    if end:
        lf = lf.filter(pl.col("timestamp") <= pl.lit(end))

    return lf


def list_available_datasets(data_dir: Path) -> dict[str, list[dict[str, str]]]:
    """Scan the data directory and return available exchanges, symbols, and file counts.

    Directory layout:
    - OHLCV: ``{data_dir}/ohlcv/{exchange}/{BASE}-{QUOTE}/{interval}/*.parquet``
    - Trades: ``{data_dir}/trades/{exchange}/{BASE}-{QUOTE}/*.parquet``
    - Tickers: ``{data_dir}/tickers/{exchange}/*.parquet``
    """
    result: dict[str, list[dict[str, str]]] = {"ohlcv": [], "trades": [], "tickers": []}

    # ── OHLCV ────────────────────────────────────────────────────────────
    ohlcv_root = data_dir / "ohlcv"
    if ohlcv_root.exists():
        for exchange_dir in sorted(ohlcv_root.iterdir()):
            if not exchange_dir.is_dir():
                continue
            for symbol_dir in sorted(exchange_dir.iterdir()):
                if not symbol_dir.is_dir():
                    continue
                file_count = sum(
                    1
                    for interval_dir in symbol_dir.iterdir()
                    if interval_dir.is_dir()
                    for f in interval_dir.glob("*.parquet")
                )
                result["ohlcv"].append(
                    {
                        "exchange": exchange_dir.name,
                        "symbol": symbol_dir.name,
                        "file_count": str(file_count),
                    }
                )

    # ── Trades ───────────────────────────────────────────────────────────
    trades_root = data_dir / "trades"
    if trades_root.exists():
        for exchange_dir in sorted(trades_root.iterdir()):
            if not exchange_dir.is_dir():
                continue
            for symbol_dir in sorted(exchange_dir.iterdir()):
                if not symbol_dir.is_dir():
                    continue
                file_count = sum(1 for f in symbol_dir.glob("*.parquet"))
                result["trades"].append(
                    {
                        "exchange": exchange_dir.name,
                        "symbol": symbol_dir.name,
                        "file_count": str(file_count),
                    }
                )

    # ── Tickers ──────────────────────────────────────────────────────────
    tickers_root = data_dir / "tickers"
    if tickers_root.exists():
        for exchange_dir in sorted(tickers_root.iterdir()):
            if not exchange_dir.is_dir():
                continue
            file_count = sum(1 for f in exchange_dir.glob("*.parquet"))
            result["tickers"].append(
                {
                    "exchange": exchange_dir.name,
                    "symbol": "all",
                    "file_count": str(file_count),
                }
            )

    return result
