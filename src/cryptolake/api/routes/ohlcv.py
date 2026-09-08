from __future__ import annotations

import datetime

import structlog
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from cryptolake.api.deps import DataDir
from cryptolake.pipeline import storage

router = APIRouter(prefix="/api/v1/ohlcv", tags=["ohlcv"])
logger = structlog.get_logger(__name__)


@router.get("/exchanges")
async def list_exchanges(data_dir: DataDir) -> list[str]:
    """List exchanges that have OHLCV data."""
    try:
        datasets = storage.list_available_datasets(data_dir)
        exchanges = sorted(
            list({item["exchange"] for item in datasets.get("ohlcv", []) if "exchange" in item})
        )
        return exchanges
    except Exception as e:
        logger.error("Failed to list exchanges", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{exchange}/{symbol}")
async def query_ohlcv(
    exchange: str,
    symbol: str,
    data_dir: DataDir,
    interval: str = Query("1h"),
    start: datetime.datetime | None = Query(None),
    end: datetime.datetime | None = Query(None),
    limit: int = Query(1000, le=10000),
    format: str = Query("json", pattern="^(json|csv)$"),
) -> Response:
    """Query OHLCV data."""
    parts = symbol.split("-")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Symbol must be in format BASE-QUOTE")

    base, quote = parts

    try:
        lf = storage.read_ohlcv(
            data_dir=data_dir,
            exchange=exchange,
            base=base,
            quote=quote,
            interval=interval,
            start=start,
            end=end,
        )

        df = lf.limit(limit).collect()

        if df.is_empty():
            raise HTTPException(status_code=404, detail="No data found")

        if format == "csv":
            csv_data = df.write_csv()
            return Response(content=csv_data, media_type="text/csv")
        else:
            json_data = df.write_json()
            return Response(content=json_data, media_type="application/json")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to query OHLCV", error=str(e), exchange=exchange, symbol=symbol)
        raise HTTPException(status_code=500, detail="Internal server error")
