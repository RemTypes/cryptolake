"""Abstract base class for all crypto exchange data sources.

Handles HTTP session management, rate limiting, retries with exponential
backoff, and structured logging. Concrete sources subclass this and implement
the ``fetch_*`` methods.
"""

from __future__ import annotations

import abc
import asyncio
import ssl
from datetime import datetime
from typing import Any

import aiohttp
import certifi
import polars as pl
import structlog
from aiohttp.client_exceptions import ClientError

logger = structlog.get_logger(__name__)


class BaseSource(abc.ABC):
    """Abstract base class for all crypto exchange data sources.

    Usage::

        async with BinanceSource() as source:
            df = await source.fetch_ohlcv("BTC", "USDT", "1h", start, end)
    """

    name: str

    def __init__(
        self,
        max_concurrent_requests: int = 10,
        max_retries: int = 3,
        base_backoff: float = 1.0,
    ) -> None:
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.session: aiohttp.ClientSession | None = None
        self.logger = logger.bind(source=self.name)

    async def __aenter__(self) -> BaseSource:
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        self.session = aiohttp.ClientSession(connector=connector)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if self.session is not None:
            await self.session.close()
            self.session = None

    async def _request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        weight: int = 1,
    ) -> Any:
        """Make an HTTP request with rate limiting and retries.

        Args:
            method: HTTP method (GET, POST, etc.).
            url: Full URL to request.
            params: Query parameters.
            headers: Extra HTTP headers.
            weight: Request weight for rate-limit accounting.

        Returns:
            Parsed JSON response (or text if not JSON).

        Raises:
            aiohttp.ClientError: After all retries are exhausted.
        """
        if self.session is None:
            msg = "Session not initialised. Use 'async with source:' context."
            raise RuntimeError(msg)

        for attempt in range(self.max_retries + 1):
            async with self.semaphore:
                try:
                    self.logger.debug(
                        "request",
                        method=method,
                        url=url,
                        attempt=attempt,
                        weight=weight,
                    )
                    async with self.session.request(
                        method, url, params=params, headers=headers
                    ) as response:
                        response.raise_for_status()
                        if response.content_type == "application/json":
                            return await response.json()
                        return await response.text()

                except ClientError as exc:
                    if attempt == self.max_retries:
                        self.logger.error(
                            "request_failed",
                            url=url,
                            error=str(exc),
                            attempts=attempt + 1,
                        )
                        raise

                    delay = self.base_backoff * (2**attempt)
                    self.logger.warning(
                        "request_retrying",
                        url=url,
                        error=str(exc),
                        delay=delay,
                        attempt=attempt,
                    )
                    await asyncio.sleep(delay)

        # unreachable — the for-loop always returns or raises
        msg = "Exhausted retries without result"  # pragma: no cover
        raise RuntimeError(msg)  # pragma: no cover

    # ── Abstract interface ───────────────────────────────────────────────

    @abc.abstractmethod
    def normalise_symbol(self, base: str, quote: str) -> str:
        """Convert a canonical (base, quote) pair to the exchange-native symbol."""

    @abc.abstractmethod
    async def fetch_ohlcv(
        self,
        base: str,
        quote: str,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> pl.DataFrame:
        """Fetch OHLCV candlestick data in the canonical schema."""

    @abc.abstractmethod
    async def fetch_trades(self, base: str, quote: str, limit: int = 500) -> pl.DataFrame:
        """Fetch recent trades in the canonical schema."""

    @abc.abstractmethod
    async def fetch_ticker(self, base: str, quote: str) -> pl.DataFrame:
        """Fetch the 24h ticker snapshot for a single pair."""

    @abc.abstractmethod
    async def fetch_tickers(self) -> pl.DataFrame:
        """Fetch all available 24h ticker snapshots."""
