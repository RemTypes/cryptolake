from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import cryptolake
from cryptolake.api.routes import compare, download, metadata, ohlcv, tickers


def create_app() -> FastAPI:
    """Create the FastAPI app."""
    app = FastAPI(
        title="CryptoLake API",
        description="Unified crypto market data — normalised across exchanges into clean Parquet",
        version=getattr(cryptolake, "__version__", "0.1.0"),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(ohlcv.router)
    app.include_router(tickers.router)
    app.include_router(compare.router)
    app.include_router(metadata.router)
    app.include_router(download.router)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "name": "CryptoLake",
            "version": getattr(cryptolake, "__version__", "0.1.0"),
            "docs": "/docs",
        }

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
