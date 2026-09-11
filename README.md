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

### 1. Backend & Data Lake
```bash
# Install Python package in editable mode
pip install -e ".[dev]"

# Ingest multi-exchange data (e.g. past 3 days across 5 exchanges)
cryptolake ingest --days 3

# Inspect & preview parquet partitions
cryptolake inspect
cryptolake inspect data/ohlcv/binance/BTC-USDT/1h/2026-09-08.parquet --rows 5

# Start the high-performance FastAPI server
cryptolake serve --port 8000
```

### 2. Next.js 15 Quantitative Terminal & Math Lab
```bash
# Navigate to frontend and install dependencies
cd frontend
npm install

# Run the development server (proxies /api/v1 to 127.0.0.1:8000)
npm run dev

# Or build and launch the production terminal
npm run build
npm run start
```
Terminal interface available at `http://localhost:3000`.

---

## Architecture & Mathematical Research Modules

CryptoLake features an integrated quantitative research workbench applying pure mathematics from 2nd-year undergraduate mathematics (Topology, Differential Geometry of Surfaces, Applied Probability, and Econometric Statistics):

1. **Topological Delay Embedding & Phase Space Reconstruction (`/api/v1/math/tda/takens`)**:
   - Reconstructs $m$-dimensional dynamical attractor manifolds from 1D scalar return streams via **Takens' Delay Embedding Theorem** ($v_t = (r_{t-2\tau}, r_{t-\tau}, r_t) \in \mathbb{R}^3$).
   - Calculates sliding-window **topological entropy** to detect phase space dimension collapses before volatility cascades.

2. **Riemannian Correlation Geometry & Multidimensional Scaling (`/api/v1/math/geometry/correlation`)**:
   - Maps cross-asset correlation matrices $\mathbf{C} \in [-1, 1]^{N \times N}$ into an ultrametric Riemannian space via Mantegna's metric $d_{ij} = \sqrt{2(1 - \rho_{ij})}$.
   - Double-centers the distance matrix ($B = -\frac{1}{2} H D^2 H$) and executes spectral eigendecomposition (Classical MDS) to embed assets into 2D/3D Euclidean geometric configurations.

3. **Statistical Microstructure & Heavy-Tailed Distributions (`/api/v1/math/stats/distribution`)**:
   - Tests financial stylized facts (Mandelbrot 1963, Cont 2001): leptokurtosis, skewness, and volatility clustering.
   - Fits parametric **Student-$t$ distributions** via Maximum Likelihood Estimation (MLE) alongside Gaussian benchmarks and Quantile-Quantile (QQ) plots.
   - Evaluates **Jarque-Bera normality hypothesis tests**.

4. **Multi-Exchange Orderbook Arbitrage & Effective Spreads (`/api/v1/math/microstructure/spreads`)**:
   - Real-time bid-ask dispersion matrices across Binance, Coinbase, Kraken, OKX, and Bybit identifying instantaneous cross-venue arbitrage basis points.

---

## API Reference

```
# Data Lake & OHLCV
GET /api/v1/ohlcv/{exchange}/{symbol}?interval=1h&start=2026-09-08&end=2026-09-11
GET /api/v1/tickers
GET /api/v1/compare/{symbol}
GET /api/v1/metadata/exchanges
GET /api/v1/metadata/symbols
GET /api/v1/download/ohlcv/{exchange}/{symbol}?interval=1h&format=parquet

# Quantitative Mathematics Lab
GET /api/v1/math/tda/takens?symbol=BTC-USDT&exchange=binance&tau=2&dim=3
GET /api/v1/math/geometry/correlation?interval=1h
GET /api/v1/math/stats/distribution?symbol=ETH-USDT&exchange=binance&interval=1h
GET /api/v1/math/microstructure/spreads?symbol=BTC-USDT
```

Interactive OpenAPI documentation available at `http://localhost:8000/docs` and built-in research documentation at `http://localhost:3000/docs`.

## Project Structure

```
cryptolake/
├── src/cryptolake/
│   ├── api/                 # FastAPI routes (ohlcv, tickers, compare, math, metadata)
│   ├── config.py            # Lake directory configuration & settings
│   ├── pipeline/            # Ingestion, schema validation, storage, normalisation
│   ├── schemas/             # PyArrow canonical schemas (OHLCV, trades, tickers)
│   ├── sources/             # Exchange adapters (Binance, Coinbase, Kraken, OKX, Bybit)
│   └── cli.py               # Rich CLI with inspect, ingest, serve, status
├── frontend/                # Next.js 15 + Tailwind + Plotly + KaTeX + Lightweight Charts
│   ├── src/app/             # Dashboard, Datasets, Terminal, Math Lab, Docs
│   └── src/components/      # 3D Plotly canvas, Candlestick, KaTeX math renderer
├── data/                    # Unified multi-exchange Apache Parquet lake
└── tests/                   # Pytest suite with 56 unit & integration tests
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
