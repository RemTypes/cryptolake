# CryptoLake 🏔️

**Unified crypto market data platform** — ingest, normalise, and serve data from multiple exchanges in clean Parquet format.

## What is this?

CryptoLake pulls market data from 5 major exchanges (Binance, Coinbase, Kraken, OKX, Bybit) and 2 aggregators (CoinGecko, CryptoCompare), normalises it all into a single consistent schema, and stores it as partitioned Parquet files. A FastAPI backend and web frontend make the data browsable and downloadable.

### The problem it solves

Every crypto exchange has its own API format:
- Coinbase returns candle columns as `[time, LOW, HIGH, open, close, volume]` (LHOCV, not OHLCV!)
- Binance returns timestamps in milliseconds, Kraken in seconds, Coinbase in ISO 8601
- Kraken calls Bitcoin `XXBTZUSD`, Binance calls it `BTCUSDT`, Coinbase calls it `BTC-USD`
- Some return data ascending, others descending

CryptoLake normalises all of this into one clean schema.

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Ingest data from Binance
cryptolake ingest --exchange binance --symbol BTC/USDT --interval 1h --start 2024-01-01

# Start the API server
cryptolake serve

# Check what data you have
cryptolake status
```

## API

```
GET /api/v1/ohlcv/{exchange}/{symbol}?interval=1h&start=2024-01-01&end=2024-06-01
GET /api/v1/tickers
GET /api/v1/metadata/exchanges
GET /api/v1/download/ohlcv/{exchange}/{symbol}
```

Full interactive docs at `http://localhost:8000/docs`.

## Project Structure

```
src/cryptolake/
├── config.py           # Settings (env vars / .env)
├── schemas/            # Canonical Parquet schemas (OHLCV, trades, tickers)
├── sources/            # Exchange adapters (Binance, CoinGecko, ...)
├── pipeline/           # Ingestion, normalisation, validation, storage
├── api/                # FastAPI application
└── cli.py              # CLI entry point
```

## Data Format

All data is stored as partitioned Apache Parquet files:

```
data/ohlcv/{exchange}/{BASE}-{QUOTE}/{interval}/{YYYY-MM-DD}.parquet
```

### Canonical OHLCV Schema

| Column | Type | Description |
|:---|:---|:---|
| `timestamp` | `datetime[ms, UTC]` | Candle open time |
| `exchange` | `categorical` | Source exchange |
| `base` | `string` | Base asset (BTC, ETH, ...) |
| `quote` | `string` | Quote asset (USDT, USD, ...) |
| `interval` | `string` | Candle interval (1m, 1h, 1d, ...) |
| `open` | `float64` | Open price |
| `high` | `float64` | High price |
| `low` | `float64` | Low price |
| `close` | `float64` | Close price |
| `volume_base` | `float64` | Volume in base currency |
| `volume_quote` | `float64` | Volume in quote currency |

## Development

```bash
make dev        # Install dev dependencies
make lint       # Run ruff
make type-check # Run mypy
make test       # Run pytest
```

## Tech Stack

- **Python 3.12+** with full type annotations
- **Polars** for DataFrames (not pandas)
- **PyArrow** for Parquet I/O
- **FastAPI** for the REST API
- **Typer + Rich** for the CLI
- **aiohttp** for async HTTP

## License

MIT
