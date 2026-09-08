from __future__ import annotations

import datetime
import io

import polars as pl
import structlog
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response

from cryptolake.api.deps import DataDir

router = APIRouter(prefix="/api/v1/download", tags=["download"])
logger = structlog.get_logger(__name__)


@router.get("/{dataset}/{exchange}/{symbol}")
async def download_parquet(
    dataset: str,
    exchange: str,
    symbol: str,
    data_dir: DataDir,
    interval: str | None = Query(None),
    start: datetime.datetime | None = Query(None),
    end: datetime.datetime | None = Query(None),
) -> Response:
    """Download raw Parquet files (or merged Parquet if multiple)."""
    if dataset not in ("ohlcv", "trades", "tickers"):
        raise HTTPException(status_code=400, detail="Invalid dataset")

    parts = symbol.split("-")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Symbol must be in format BASE-QUOTE")
    base, quote = parts

    target_dir = data_dir / dataset / exchange / f"{base}-{quote}"
    if not target_dir.exists():
        raise HTTPException(status_code=404, detail="Dataset not found")

    if interval:
        search_dir = target_dir / interval
        files = sorted(list(search_dir.glob("*.parquet"))) if search_dir.exists() else []
    else:
        files = sorted(list(target_dir.glob("**/*.parquet")))

    if not files:
        raise HTTPException(status_code=404, detail="No files found")

    if len(files) == 1:
        return FileResponse(
            path=files[0],
            media_type="application/vnd.apache.parquet",
            filename=files[0].name,
        )
    else:
        # Merge multiple parquet files into a single valid parquet payload
        df = pl.read_parquet(files)
        buffer = io.BytesIO()
        df.write_parquet(buffer, compression="snappy")
        buffer.seek(0)
        return Response(
            content=buffer.getvalue(),
            media_type="application/vnd.apache.parquet",
            headers={
                "Content-Disposition": f'attachment; filename="{dataset}_{exchange}_{symbol}.parquet"'
            },
        )
