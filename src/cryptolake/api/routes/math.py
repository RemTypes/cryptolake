"""Mathematical research endpoints for quantitative finance and topology."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import polars as pl
import structlog
from fastapi import APIRouter, HTTPException, Query
from scipy import stats

from cryptolake.api.deps import DataDir
from cryptolake.pipeline import storage

router = APIRouter(prefix="/api/v1/math", tags=["math"])
logger = structlog.get_logger(__name__)


def _sanitize_float(val: float | None) -> float | None:
    if val is None or math.isnan(val) or math.isinf(val):
        return None
    return float(val)


@router.get("/tda/takens")
async def get_takens_embedding(
    data_dir: DataDir,
    symbol: str = Query(default="BTC-USDT", description="Pair symbol (e.g. BTC-USDT)"),
    exchange: str = Query(default="binance", description="Exchange name"),
    interval: str = Query(default="1h", description="Candle interval"),
    tau: int = Query(default=2, ge=1, le=24, description="Embedding delay tau"),
    dim: int = Query(default=3, ge=2, le=5, description="Embedding dimension"),
    max_points: int = Query(default=300, ge=20, le=1000, description="Max candles to use"),
) -> dict[str, Any]:
    """Compute Takens' Delay Embedding into phase space from price series.

    Extracts log returns r_t = ln(P_t / P_{t-1}) and embeds into R^dim:
    v_t = (r_{t - (dim-1)*tau}, ..., r_t).
    Also estimates optimal delay tau and rolling topological dispersion.
    """
    parts = symbol.split("-")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Symbol must be formatted as BASE-QUOTE")
    base, quote = parts

    lf = storage.read_ohlcv(
        data_dir=data_dir,
        exchange=exchange,
        base=base,
        quote=quote,
        interval=interval,
    )
    cols = lf.collect_schema().names()
    if not cols:
        raise HTTPException(
            status_code=404, detail=f"No OHLCV data found for {exchange} {symbol} {interval}"
        )

    df = lf.sort("timestamp").collect()
    if df.is_empty():
        raise HTTPException(
            status_code=404, detail=f"No OHLCV data found for {exchange} {symbol} {interval}"
        )
    if df.height < (dim * tau + 5):
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient candles ({df.height}) for dim={dim}, tau={tau}",
        )

    # Use the most recent max_points
    if df.height > max_points:
        df = df.tail(max_points)

    close_prices = df["close"].to_numpy()
    timestamps = [str(ts) for ts in df["timestamp"].to_list()]

    # Compute log returns: r_t = ln(P_t / P_{t-1})
    log_returns = np.diff(np.log(close_prices))
    n_ret = len(log_returns)

    # Optimal tau estimation: first lag where autocorrelation drops below 1/e
    autocorr = [1.0]
    for lag in range(1, min(20, n_ret // 4)):
        if n_ret - lag > 1:
            c = np.corrcoef(log_returns[:-lag], log_returns[lag:])[0, 1]
            autocorr.append(float(c) if not math.isnan(c) else 0.0)

    optimal_tau = 1
    for lag, val in enumerate(autocorr[1:], start=1):
        if val < (1.0 / math.e):
            optimal_tau = lag
            break

    # Build Takens vectors
    points: list[dict[str, Any]] = []
    min_idx = (dim - 1) * tau
    for t in range(min_idx, n_ret):
        coords: list[float] = [float(log_returns[t - (dim - 1 - i) * tau]) for i in range(dim)]
        pt: dict[str, Any] = {
            "index": t,
            "timestamp": timestamps[t + 1],
            "price": float(close_prices[t + 1]),
            "return": float(log_returns[t]),
            "x": coords[0],
            "y": coords[1],
            "z": coords[2] if dim >= 3 else 0.0,
        }
        points.append(pt)

    # Rolling topological dispersion / entropy proxy over sliding window of 30 points
    entropy_series: list[dict[str, Any]] = []
    window_size = min(30, len(points))
    if len(points) >= window_size:
        pts_arr = np.array([[p["x"], p["y"], p["z"]] for p in points])
        for i in range(window_size, len(points) + 1):
            sub = pts_arr[i - window_size : i]
            # Pairwise distances
            diff = sub[:, np.newaxis, :] - sub[np.newaxis, :, :]
            dists = np.sqrt(np.sum(diff**2, axis=-1)).flatten()
            dists = dists[dists > 1e-9]
            if len(dists) > 0:
                hist, _ = np.histogram(dists, bins=10, density=True)
                p_k = hist[hist > 0]
                p_k = p_k / np.sum(p_k)
                entropy = -float(np.sum(p_k * np.log(p_k)))
            else:
                entropy = 0.0
            entropy_series.append(
                {
                    "timestamp": points[i - 1]["timestamp"],
                    "entropy": round(entropy, 4),
                    "price": points[i - 1]["price"],
                }
            )

    return {
        "symbol": symbol,
        "exchange": exchange,
        "interval": interval,
        "tau": tau,
        "dim": dim,
        "optimal_tau_estimated": optimal_tau,
        "point_count": len(points),
        "autocorrelation": [round(a, 4) for a in autocorr],
        "points": points,
        "entropy_series": entropy_series,
        "formula": "v_t = (r_{t - 2\\tau}, r_{t - \\tau}, r_t) \\in \\mathbb{R}^3",
    }


@router.get("/geometry/correlation")
async def get_correlation_geometry(
    data_dir: DataDir,
    interval: str = Query(default="1h", description="Candle interval"),
) -> dict[str, Any]:
    """Compute Riemannian distance metric space and MDS embedding across venues & symbols.

    Calculates pairwise correlation rho_{ij}, Riemannian distance d_{ij} = sqrt(2(1 - rho_{ij})),
    and Classical Multidimensional Scaling (MDS) coordinates in 2D and 3D.
    """
    settings_data_dir = data_dir / "ohlcv"
    if not settings_data_dir.exists():
        raise HTTPException(status_code=404, detail="No OHLCV dataset directory found")

    # Find all available exchange/symbol directories
    series_map: dict[str, pl.DataFrame] = {}
    for exch_dir in sorted(settings_data_dir.iterdir()):
        if not exch_dir.is_dir() or exch_dir.name.startswith("."):
            continue
        for sym_dir in sorted(exch_dir.iterdir()):
            if not sym_dir.is_dir() or sym_dir.name.startswith("."):
                continue
            int_dir = sym_dir / interval
            if not int_dir.exists():
                continue
            parquet_files = sorted(int_dir.glob("*.parquet"))
            if not parquet_files:
                continue

            try:
                lf = pl.scan_parquet(str(int_dir / "*.parquet"))
                df = lf.select(["timestamp", "close"]).sort("timestamp").collect()
                if df.height >= 20:
                    label = f"{exch_dir.name.capitalize()}:{sym_dir.name}"
                    series_map[label] = df
            except Exception as e:
                logger.warning(
                    "failed to scan series", label=f"{exch_dir.name}:{sym_dir.name}", err=str(e)
                )

    if len(series_map) < 3:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least 3 distinct series to compute geometry, found {len(series_map)}",
        )

    # Pick top 10 series with most data points to keep matrix clean
    labels = list(series_map.keys())[:10]

    # Align on common timestamps
    base_df = series_map[labels[0]].select(pl.col("timestamp"))
    for lbl in labels:
        s_df = series_map[lbl].rename({"close": lbl})
        base_df = base_df.join(s_df, on="timestamp", how="inner")

    if base_df.height < 10:
        # Fallback to outer with forward fill
        base_df = series_map[labels[0]].select(pl.col("timestamp"))
        for lbl in labels:
            s_df = series_map[lbl].rename({"close": lbl})
            base_df = base_df.join(s_df, on="timestamp", how="full").sort("timestamp")
        base_df = base_df.fill_null(strategy="forward").drop_nulls()

    if base_df.height < 10:
        raise HTTPException(status_code=400, detail="Insufficient aligned timestamps across series")

    # Compute log returns matrix
    price_matrix = base_df.select(labels).to_numpy()
    ret_matrix = np.diff(np.log(price_matrix), axis=0)

    # Correlation matrix C (N x N)
    corr_matrix = np.corrcoef(ret_matrix, rowvar=False)
    n = len(labels)
    # Clamp to [-1, 1] to prevent numerical issues
    corr_matrix = np.clip(corr_matrix, -1.0, 1.0)
    for i in range(n):
        corr_matrix[i, i] = 1.0

    # Metric distance matrix D_ij = sqrt(2 * (1 - C_ij))
    dist_matrix = np.sqrt(np.maximum(2.0 * (1.0 - corr_matrix), 0.0))

    # Classical Multidimensional Scaling (MDS)
    # Gram matrix B = -0.5 * H * D^2 * H, where H = I - (1/n)*11^T
    h_mat = np.eye(n) - np.ones((n, n)) / n
    d_sq = dist_matrix**2
    b_gram = -0.5 * h_mat @ d_sq @ h_mat

    # Eigen-decomposition
    eigvals, eigvecs = np.linalg.eigh(b_gram)
    # Sort descending
    idx = np.argsort(eigvals)[::-1]
    eigvals = eigvals[idx]
    eigvecs = eigvecs[:, idx]

    # Positive eigenvalues only for coordinates
    pos_eigvals = np.maximum(eigvals, 0.0)
    total_var = np.sum(pos_eigvals) if np.sum(pos_eigvals) > 0 else 1.0
    explained_var = [float(round(v / total_var, 4)) for v in pos_eigvals[: min(5, n)]]

    # 2D and 3D embeddings
    coords_2d: list[dict[str, Any]] = []
    coords_3d: list[dict[str, Any]] = []

    scale_2d = np.sqrt(pos_eigvals[:2])
    x_2d = eigvecs[:, :2] * scale_2d

    scale_3d = (
        np.sqrt(pos_eigvals[:3])
        if len(pos_eigvals) >= 3
        else np.pad(np.sqrt(pos_eigvals), (0, 3 - len(pos_eigvals)))
    )
    x_3d = eigvecs[:, : min(3, n)] * scale_3d[: min(3, n)]

    for i, lbl in enumerate(labels):
        parts_lbl = lbl.split(":")
        venue = parts_lbl[0]
        sym = parts_lbl[1] if len(parts_lbl) > 1 else ""
        coords_2d.append(
            {
                "label": lbl,
                "venue": venue,
                "symbol": sym,
                "x": round(float(x_2d[i, 0]), 4),
                "y": round(float(x_2d[i, 1]), 4),
            }
        )
        coords_3d.append(
            {
                "label": lbl,
                "venue": venue,
                "symbol": sym,
                "x": round(float(x_3d[i, 0]), 4),
                "y": round(float(x_3d[i, 1]), 4),
                "z": round(float(x_3d[i, 2]) if x_3d.shape[1] >= 3 else 0.0, 4),
            }
        )

    return {
        "labels": labels,
        "sample_count": int(base_df.height),
        "correlation_matrix": [[round(float(val), 4) for val in row] for row in corr_matrix],
        "distance_matrix": [[round(float(val), 4) for val in row] for row in dist_matrix],
        "coords_2d": coords_2d,
        "coords_3d": coords_3d,
        "eigenvalues": [round(float(ev), 4) for ev in eigvals[:5]],
        "explained_variance_ratio": explained_var,
        "metric_formula": "d_{ij} = \\sqrt{2(1 - \\rho_{ij})}",
    }


@router.get("/stats/distribution")
async def get_distribution_stats(
    data_dir: DataDir,
    symbol: str = Query(default="BTC-USDT", description="Pair symbol"),
    exchange: str = Query(default="binance", description="Exchange name"),
    interval: str = Query(default="1h", description="Candle interval"),
) -> dict[str, Any]:
    """Compute empirical return distributions, fat-tail fits, and QQ plot coordinates."""
    parts = symbol.split("-")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Symbol must be formatted as BASE-QUOTE")
    base, quote = parts

    lf = storage.read_ohlcv(
        data_dir=data_dir,
        exchange=exchange,
        base=base,
        quote=quote,
        interval=interval,
    )
    cols = lf.collect_schema().names()
    if not cols:
        raise HTTPException(
            status_code=404, detail=f"No OHLCV data found for {exchange} {symbol} {interval}"
        )

    df = lf.sort("timestamp").collect()
    if df.is_empty():
        raise HTTPException(
            status_code=404, detail=f"No OHLCV data found for {exchange} {symbol} {interval}"
        )
    if df.height < 15:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient candles ({df.height}) for statistical distribution",
        )

    close_prices = df["close"].to_numpy()
    log_returns = np.diff(np.log(close_prices))
    n = len(log_returns)

    # Statistical moments
    mean_ret = float(np.mean(log_returns))
    std_ret = float(np.std(log_returns, ddof=1)) if n > 1 else 0.0
    skew_val = float(stats.skew(log_returns)) if std_ret > 0 else 0.0
    kurt_excess = float(stats.kurtosis(log_returns)) if std_ret > 0 else 0.0

    # Jarque-Bera normality test
    jb_stat, jb_pvalue = stats.jarque_bera(log_returns)

    # Student-t distribution fit
    try:
        t_df, t_loc, t_scale = stats.t.fit(log_returns)
    except Exception:
        t_df, t_loc, t_scale = 3.0, mean_ret, std_ret

    # Histogram calculation
    hist_counts, bin_edges = np.histogram(log_returns, bins=25, density=True)
    bin_centers = [(bin_edges[i] + bin_edges[i + 1]) / 2.0 for i in range(len(hist_counts))]
    histogram_data = [
        {"center": round(float(bc), 6), "density": round(float(d), 4)}
        for bc, d in zip(bin_centers, hist_counts, strict=False)
    ]

    # Evaluate fitted curves over linspace
    x_eval = np.linspace(float(bin_edges[0]), float(bin_edges[-1]), 100)
    norm_pdf = (
        stats.norm.pdf(x_eval, loc=mean_ret, scale=std_ret)
        if std_ret > 0
        else np.zeros_like(x_eval)
    )
    t_pdf = stats.t.pdf(x_eval, df=t_df, loc=t_loc, scale=t_scale)

    fitted_curves = [
        {
            "x": round(float(x), 6),
            "normal_pdf": round(float(n_p), 4),
            "student_t_pdf": round(float(t_p), 4),
        }
        for x, n_p, t_p in zip(x_eval, norm_pdf, t_pdf, strict=False)
    ]

    # Quantile-Quantile (QQ) plot coordinates vs Standard Normal
    # Sorted sample returns standardized
    z_scores = (log_returns - mean_ret) / std_ret if std_ret > 0 else np.zeros_like(log_returns)
    sorted_sample = np.sort(z_scores)
    # Theoretical quantiles
    probs = (np.arange(1, n + 1) - 0.5) / n
    theoretical_quantiles = stats.norm.ppf(probs)

    # Subsample QQ points if large
    stride = max(1, n // 80)
    qq_points = [
        {
            "theoretical": round(float(t_q), 4),
            "sample": round(float(s_q), 4),
        }
        for t_q, s_q in zip(theoretical_quantiles[::stride], sorted_sample[::stride], strict=False)
    ]

    return {
        "symbol": symbol,
        "exchange": exchange,
        "interval": interval,
        "sample_size": n,
        "moments": {
            "mean": round(mean_ret, 6),
            "std_dev": round(std_ret, 6),
            "skewness": round(skew_val, 4),
            "excess_kurtosis": round(kurt_excess, 4),
            "is_leptokurtic": kurt_excess > 0,
        },
        "jarque_bera": {
            "statistic": round(float(jb_stat), 4),
            "p_value": _sanitize_float(jb_pvalue),
            "is_normal_rejected": bool(jb_pvalue < 0.05),
        },
        "student_t_fit": {
            "degrees_of_freedom": round(float(t_df), 2),
            "location": round(float(t_loc), 6),
            "scale": round(float(t_scale), 6),
        },
        "histogram": histogram_data,
        "fitted_curves": fitted_curves,
        "qq_plot": qq_points,
    }


@router.get("/microstructure/spreads")
async def get_microstructure_spreads(
    data_dir: DataDir,
    symbol: str = Query(default="BTC-USDT", description="Pair symbol"),
) -> dict[str, Any]:
    """Analyze cross-venue ticker spreads and arbitrage opportunities across the lake."""
    parts = symbol.split("-")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Symbol must be formatted as BASE-QUOTE")
    base, quote = parts

    lf = storage.read_tickers(data_dir=data_dir, base=base, quote=quote)
    cols = lf.collect_schema().names()
    if not cols:
        raise HTTPException(status_code=404, detail=f"No ticker data found for {symbol}")

    df = lf.sort("timestamp", descending=True).collect()
    if df.is_empty():
        raise HTTPException(status_code=404, detail=f"No tickers found for {symbol}")

    # Deduplicate to get latest quote per exchange
    latest_per_exch = df.unique(subset=["exchange"], keep="first")
    venues: list[dict[str, Any]] = []

    for row in latest_per_exch.iter_rows(named=True):
        bid = _sanitize_float(row.get("bid_price"))
        ask = _sanitize_float(row.get("ask_price"))
        last = _sanitize_float(row.get("last_price"))
        spread_bps = None
        if bid is not None and ask is not None and ask > 0:
            spread_bps = round(((ask - bid) / ask) * 10000.0, 2)

        venues.append(
            {
                "exchange": row.get("exchange"),
                "bid": bid,
                "ask": ask,
                "last": last,
                "spread_bps": spread_bps,
                "volume_24h": _sanitize_float(row.get("volume_24h_quote")),
                "timestamp": str(row.get("timestamp")),
            }
        )

    valid_asks = [(v["exchange"], v["ask"]) for v in venues if v["ask"] is not None]
    valid_bids = [(v["exchange"], v["bid"]) for v in venues if v["bid"] is not None]

    arb_opp = None
    if valid_asks and valid_bids:
        cheapest_venue, min_ask = min(valid_asks, key=lambda x: x[1])
        richest_venue, max_bid = max(valid_bids, key=lambda x: x[1])
        delta_bps = round(((max_bid - min_ask) / min_ask) * 10000.0, 2)
        arb_opp = {
            "buy_venue": cheapest_venue,
            "buy_price": min_ask,
            "sell_venue": richest_venue,
            "sell_price": max_bid,
            "gross_arbitrage_bps": delta_bps,
            "is_profitable": delta_bps > 0,
        }

    return {
        "symbol": symbol,
        "venue_count": len(venues),
        "venues": venues,
        "arbitrage": arb_opp,
    }
