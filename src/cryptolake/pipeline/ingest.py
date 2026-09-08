from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl
import structlog

if TYPE_CHECKING:
    from cryptolake.sources.base import BaseSource

from cryptolake.pipeline.storage import write_ohlcv, write_tickers
from cryptolake.pipeline.validate import validate_ohlcv, validate_ticker

logger = structlog.get_logger()


@dataclass
class IngestReport:
    source: str
    dataset: str
    rows_written: int
    files_created: int
    errors: list[str]
    duration_seconds: float


async def ingest_ohlcv(
    sources: list[BaseSource],
    symbols: list[tuple[str, str]],
    intervals: list[str],
    start: datetime,
    end: datetime,
    data_dir: Path,
) -> list[IngestReport]:

    async def process_source(source: BaseSource) -> IngestReport:
        t0 = time.time()
        rows_written = 0
        files_created = 0
        errors = []

        # Per-source semaphore to respect rate limits
        sem = asyncio.Semaphore(source.rate_limit if hasattr(source, "rate_limit") else 5)

        async def process_item(base: str, quote: str, interval: str) -> None:
            nonlocal rows_written, files_created
            async with sem:
                try:
                    logger.info(
                        "fetching ohlcv",
                        source=source.name,
                        base=base,
                        quote=quote,
                        interval=interval,
                    )
                    df = await source.fetch_ohlcv(base, quote, interval, start, end)
                    if df is not None and df.height > 0:
                        val_res = validate_ohlcv(df)
                        if not val_res.is_valid:
                            errors.extend(
                                [f"{base}-{quote}-{interval}: {e}" for e in val_res.errors]
                            )

                        # Write anyway for now, or could filter out bad data
                        write_ohlcv(df, data_dir)
                        rows_written += df.height

                        # We don't have an exact count of files written from write_ohlcv easily,
                        # but we can approximate it as 1 per day if we wanted.
                        files_created += df.select(pl.col("timestamp").dt.date()).n_unique()
                except Exception as e:
                    logger.error(
                        "error fetching ohlcv",
                        source=source.name,
                        base=base,
                        quote=quote,
                        interval=interval,
                        error=str(e),
                    )
                    errors.append(
                        f"Error fetching OHLCV for {source.name} {base}/{quote} {interval}: {e}"
                    )

        tasks = [
            process_item(base, quote, interval) for base, quote in symbols for interval in intervals
        ]

        await asyncio.gather(*tasks)

        duration = time.time() - t0
        return IngestReport(source.name, "ohlcv", rows_written, files_created, errors, duration)

    results = await asyncio.gather(*(process_source(s) for s in sources))
    return list(results)


async def ingest_tickers(sources: list[BaseSource], data_dir: Path) -> list[IngestReport]:

    async def process_source(source: BaseSource) -> IngestReport:
        t0 = time.time()
        rows_written = 0
        files_created = 0
        errors = []

        try:
            logger.info("fetching tickers", source=source.name)
            df = await source.fetch_tickers()
            if df is not None and df.height > 0:
                val_res = validate_ticker(df)
                if not val_res.is_valid:
                    errors.extend(val_res.errors)

                write_tickers(df, data_dir)
                rows_written += df.height
                files_created += 1
        except Exception as e:
            logger.error("error fetching tickers", source=source.name, error=str(e))
            errors.append(f"Error fetching tickers for {source.name}: {e}")

        duration = time.time() - t0
        return IngestReport(source.name, "tickers", rows_written, files_created, errors, duration)

    results = await asyncio.gather(*(process_source(s) for s in sources))
    return list(results)
