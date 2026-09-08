from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException

from cryptolake.api.deps import DataDir
from cryptolake.pipeline import storage

router = APIRouter(prefix="/api/v1/metadata", tags=["metadata"])
logger = structlog.get_logger(__name__)


@router.get("/exchanges")
async def list_metadata_exchanges(data_dir: DataDir) -> list[str]:
    """List available exchanges."""
    try:
        datasets = storage.list_available_datasets(data_dir)
        exchanges: set[str] = set()
        for items in datasets.values():
            if isinstance(items, list):
                for item in items:
                    if item.get("exchange"):
                        exchanges.add(item["exchange"])
        return sorted(list(exchanges))
    except Exception as e:
        logger.error("Failed to list metadata exchanges", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/symbols")
async def list_metadata_symbols(data_dir: DataDir) -> dict[str, list[str]]:
    """List all normalised symbols with which exchanges have them."""
    try:
        datasets = storage.list_available_datasets(data_dir)
        symbols_map: dict[str, set[str]] = {}
        for items in datasets.values():
            if isinstance(items, list):
                for item in items:
                    sym = item.get("symbol")
                    exch = item.get("exchange")
                    if sym and exch and sym != "all":
                        symbols_map.setdefault(sym, set()).add(exch)
        return {k: sorted(list(v)) for k, v in sorted(symbols_map.items())}
    except Exception as e:
        logger.error("Failed to list symbols", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status")
async def ingestion_status(data_dir: DataDir) -> dict[str, Any]:
    """Ingestion status (latest data timestamps per source)."""
    try:
        datasets = storage.list_available_datasets(data_dir)
        return {"status": "ok", "datasets": datasets}
    except Exception as e:
        logger.error("Failed to get status", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
