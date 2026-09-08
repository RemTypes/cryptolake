from __future__ import annotations

import polars as pl
import structlog
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from cryptolake.api.deps import DataDir
from cryptolake.pipeline import storage

router = APIRouter(prefix="/api/v1/tickers", tags=["tickers"])
logger = structlog.get_logger(__name__)


@router.get("")
async def get_all_tickers(
    data_dir: DataDir,
    exchange: str | None = Query(None),
    limit: int = Query(100),
) -> Response:
    """Latest tickers across all exchanges."""
    try:
        lf = storage.read_tickers(data_dir=data_dir, exchange=exchange, start=None, end=None)
        cols = lf.collect_schema().names()
        if "timestamp" in cols:
            lf = lf.sort("timestamp", descending=True)

        df = lf.limit(limit).collect()

        json_data = df.write_json()
        return Response(content=json_data, media_type="application/json")
    except Exception as e:
        logger.error("Failed to read tickers", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{exchange}")
async def get_exchange_tickers(
    exchange: str,
    data_dir: DataDir,
    limit: int = Query(100),
) -> Response:
    """Tickers for one exchange."""
    try:
        lf = storage.read_tickers(data_dir=data_dir, exchange=exchange, start=None, end=None)
        cols = lf.collect_schema().names()
        if "timestamp" in cols:
            lf = lf.sort("timestamp", descending=True)

        df = lf.limit(limit).collect()
        if df.is_empty():
            raise HTTPException(status_code=404, detail="No data found")

        json_data = df.write_json()
        return Response(content=json_data, media_type="application/json")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to read tickers for exchange", error=str(e), exchange=exchange)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{exchange}/{symbol}")
async def get_single_ticker(
    exchange: str,
    symbol: str,
    data_dir: DataDir,
    limit: int = Query(1),
) -> Response:
    """Single ticker."""
    try:
        lf = storage.read_tickers(data_dir=data_dir, exchange=exchange, start=None, end=None)
        cols = lf.collect_schema().names()

        if "symbol" in cols:
            lf = lf.filter(pl.col("symbol") == symbol)

        if "timestamp" in cols:
            lf = lf.sort("timestamp", descending=True)

        df = lf.limit(limit).collect()
        if df.is_empty():
            raise HTTPException(status_code=404, detail="No data found")

        json_data = df.write_json()
        return Response(content=json_data, media_type="application/json")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to read single ticker", error=str(e), exchange=exchange, symbol=symbol)
        raise HTTPException(status_code=500, detail="Internal server error")
