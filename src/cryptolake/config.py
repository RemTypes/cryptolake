"""Application configuration via environment variables and .env files."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """CryptoLake application settings.

    Values are loaded from environment variables (prefixed with ``CRYPTOLAKE_``)
    and ``.env`` files.
    """

    model_config = SettingsConfigDict(
        env_prefix="CRYPTOLAKE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Storage ──────────────────────────────────────────────────────────
    data_dir: Path = Field(
        default=Path("data"),
        description="Root directory for Parquet output files.",
    )
    metadata_db: Path = Field(
        default=Path("data/metadata.db"),
        description="Path to the SQLite metadata database.",
    )

    # ── API Keys (optional, for aggregators) ─────────────────────────────
    coingecko_api_key: str = Field(
        default="",
        description="CoinGecko demo API key (free tier).",
    )
    cryptocompare_api_key: str = Field(
        default="",
        description="CryptoCompare API key.",
    )

    # ── Rate Limiting ────────────────────────────────────────────────────
    binance_rate_limit_rpm: int = Field(
        default=1000,
        description="Binance: max request weight per minute (conservative).",
    )
    coinbase_rate_limit_rps: int = Field(
        default=10,
        description="Coinbase: max requests per second.",
    )
    kraken_rate_limit_rps: float = Field(
        default=1.0,
        description="Kraken: max requests per second (conservative).",
    )
    okx_rate_limit_rps: int = Field(
        default=18,
        description="OKX: max requests per second (conservative under 20/s).",
    )
    bybit_rate_limit_rps: int = Field(
        default=100,
        description="Bybit: max requests per second (conservative under 120/s).",
    )
    coingecko_rate_limit_rpm: int = Field(
        default=25,
        description="CoinGecko: max requests per minute (free tier).",
    )

    # ── Ingestion ────────────────────────────────────────────────────────
    default_symbols: list[str] = Field(
        default=["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"],
        description="Default trading pairs to ingest.",
    )
    default_intervals: list[str] = Field(
        default=["1m", "1h", "1d"],
        description="Default candle intervals to ingest.",
    )

    # ── API Server ───────────────────────────────────────────────────────
    api_host: str = Field(default="0.0.0.0", description="API bind host.")
    api_port: int = Field(default=8000, description="API bind port.")

    @property
    def ohlcv_dir(self) -> Path:
        """Directory for OHLCV Parquet files."""
        return self.data_dir / "ohlcv"

    @property
    def trades_dir(self) -> Path:
        """Directory for trade Parquet files."""
        return self.data_dir / "trades"

    @property
    def tickers_dir(self) -> Path:
        """Directory for ticker snapshot Parquet files."""
        return self.data_dir / "tickers"

    @property
    def metadata_dir(self) -> Path:
        """Directory for metadata Parquet files."""
        return self.data_dir / "metadata"


def get_settings() -> Settings:
    """Create and return a Settings instance."""
    return Settings()
