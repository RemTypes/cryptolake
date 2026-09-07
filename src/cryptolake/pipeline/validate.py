from __future__ import annotations

from dataclasses import dataclass

import polars as pl
import structlog

logger = structlog.get_logger()


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    row_count: int
    invalid_row_count: int


def validate_ohlcv(df: pl.DataFrame) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    row_count = df.height
    invalid_row_count = 0

    if row_count == 0:
        return ValidationResult(True, errors, warnings, 0, 0)

    # Check for null timestamps
    null_ts = df.filter(pl.col("timestamp").is_null()).height
    if null_ts > 0:
        errors.append(f"{null_ts} rows with null timestamps")
        invalid_row_count += null_ts

    # Check high >= low, high >= open, high >= close
    bad_high = df.filter(
        (pl.col("high") < pl.col("low"))
        | (pl.col("high") < pl.col("open"))
        | (pl.col("high") < pl.col("close"))
    ).height
    if bad_high > 0:
        errors.append(f"{bad_high} rows with invalid high prices")
        invalid_row_count += bad_high

    # Check low <= open, low <= close
    bad_low = df.filter((pl.col("low") > pl.col("open")) | (pl.col("low") > pl.col("close"))).height
    if bad_low > 0:
        errors.append(f"{bad_low} rows with invalid low prices")
        invalid_row_count += bad_low

    # Check positive prices and non-negative volume
    bad_vals = df.filter(
        (pl.col("open") <= 0) | (pl.col("close") <= 0) | (pl.col("volume_base") < 0)
    ).height
    if bad_vals > 0:
        errors.append(f"{bad_vals} rows with non-positive prices or negative volume")
        invalid_row_count += bad_vals

    # Check duplicates
    if (
        "exchange" in df.columns
        and "base" in df.columns
        and "quote" in df.columns
        and "interval" in df.columns
    ):
        dups = (
            df.group_by(["timestamp", "exchange", "base", "quote", "interval"])
            .len()
            .filter(pl.col("len") > 1)
            .height
        )
        if dups > 0:
            errors.append(f"{dups} duplicate timestamp entries")
            invalid_row_count += dups

    # Monotonically increasing timestamps check (if sorted by timestamp per group)
    if (
        "exchange" in df.columns
        and "base" in df.columns
        and "quote" in df.columns
        and "interval" in df.columns
    ):
        is_sorted = (
            df.sort(["exchange", "base", "quote", "interval", "timestamp"])
            .select(pl.col("timestamp").is_sorted().alias("sorted"))
            .item()
        )
        if not is_sorted:
            errors.append("Timestamps are not monotonically increasing")

    is_valid = len(errors) == 0
    return ValidationResult(is_valid, errors, warnings, row_count, invalid_row_count)


def validate_trades(df: pl.DataFrame) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    row_count = df.height
    invalid_row_count = 0

    if row_count == 0:
        return ValidationResult(True, errors, warnings, 0, 0)

    # Check nulls
    null_cols = df.select(
        [
            pl.col("timestamp").is_null().sum().alias("ts"),
            pl.col("price").is_null().sum().alias("px"),
        ]
    ).row(0)

    if null_cols[0] > 0 or null_cols[1] > 0:
        errors.append(f"Nulls found: timestamps={null_cols[0]}, prices={null_cols[1]}")
        invalid_row_count += max(null_cols)

    # Check positive values
    bad_vals = df.filter((pl.col("price") <= 0) | (pl.col("quantity") <= 0)).height
    if bad_vals > 0:
        errors.append(f"{bad_vals} rows with non-positive price or quantity")
        invalid_row_count += bad_vals

    # Check side
    bad_sides = df.filter(~pl.col("side").is_in(["buy", "sell"])).height
    if bad_sides > 0:
        errors.append(f"{bad_sides} rows with invalid side (not buy/sell)")
        invalid_row_count += bad_sides

    # Check duplicate trade_ids per exchange
    if "exchange" in df.columns and "trade_id" in df.columns:
        dups = df.group_by(["exchange", "trade_id"]).len().filter(pl.col("len") > 1).height
        if dups > 0:
            errors.append(f"{dups} duplicate trade_ids found")
            invalid_row_count += dups

    is_valid = len(errors) == 0
    return ValidationResult(is_valid, errors, warnings, row_count, invalid_row_count)


def validate_ticker(df: pl.DataFrame) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    row_count = df.height
    invalid_row_count = 0

    if row_count == 0:
        return ValidationResult(True, errors, warnings, 0, 0)

    bad_prices = df.filter(
        (pl.col("last_price") <= 0) | (pl.col("bid_price") <= 0) | (pl.col("ask_price") <= 0)
    ).height

    if bad_prices > 0:
        errors.append(f"{bad_prices} rows with non-positive prices")
        invalid_row_count += bad_prices

    crossed = df.filter(pl.col("ask_price") < pl.col("bid_price")).height
    if crossed > 0:
        warnings.append(f"{crossed} rows with crossed markets (ask < bid)")

    bad_24h = df.filter(pl.col("high_24h") < pl.col("low_24h")).height
    if bad_24h > 0:
        errors.append(f"{bad_24h} rows with high_24h < low_24h")
        invalid_row_count += bad_24h

    is_valid = len(errors) == 0
    return ValidationResult(is_valid, errors, warnings, row_count, invalid_row_count)
