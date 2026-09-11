"""Cross-exchange price comparison and arbitrage metrics route."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException

from cryptolake.api.deps import DataDir
from cryptolake.pipeline import storage

router = APIRouter(prefix="/api/v1/compare", tags=["compare"])
logger = structlog.get_logger(__name__)


@router.get("/{symbol}")
async def compare_prices(
    symbol: str,
    data_dir: DataDir,
) -> dict[str, Any]:
    """Compare prices and calculate cross-exchange spread and arbitrage opportunity.

    - **symbol**: Pair in canonical format (e.g. ``BTC-USDT`` or ``BTC-USD``).
    - Returns per-exchange quotes, highest/lowest venues, cross-venue spread in basis points (bps),
      and gross cross-market arbitrage opportunity.
    """
    parts = symbol.split("-")
    if len(parts) != 2:
        raise HTTPException(
            status_code=400, detail="Symbol must be in canonical format BASE-QUOTE (e.g. BTC-USDT)"
        )
    base, quote = parts

    try:
        # First check latest tickers
        lf = storage.read_tickers(data_dir=data_dir, base=base, quote=quote)
        cols = lf.collect_schema().names()
        if "timestamp" in cols:
            lf = lf.sort("timestamp", descending=True)
        tickers_df = lf.collect()

        venues: list[dict[str, Any]] = []

        if not tickers_df.is_empty():
            # Deduplicate by exchange to get latest quote per exchange
            latest_per_exch = tickers_df.unique(subset=["exchange"], keep="first")
            for row in latest_per_exch.iter_rows(named=True):
                ts = row.get("timestamp")
                venues.append(
                    {
                        "exchange": row.get("exchange"),
                        "last_price": row.get("last_price"),
                        "bid_price": row.get("bid_price"),
                        "ask_price": row.get("ask_price"),
                        "volume_24h_quote": row.get("volume_24h_quote"),
                        "timestamp": str(ts) if ts is not None else None,
                    }
                )

        # If tickers are empty, fallback to latest OHLCV close across available exchanges
        if not venues:
            ohlcv_lf = storage.read_ohlcv(data_dir=data_dir, base=base, quote=quote)
            ohlcv_cols = ohlcv_lf.collect_schema().names()
            if "timestamp" in ohlcv_cols:
                ohlcv_lf = ohlcv_lf.sort("timestamp", descending=True)
            ohlcv_df = ohlcv_lf.collect()

            if not ohlcv_df.is_empty():
                latest_ohlcv = ohlcv_df.unique(subset=["exchange"], keep="first")
                for row in latest_ohlcv.iter_rows(named=True):
                    close_px = row.get("close")
                    ts = row.get("timestamp")
                    venues.append(
                        {
                            "exchange": row.get("exchange"),
                            "last_price": close_px,
                            "bid_price": close_px,
                            "ask_price": close_px,
                            "volume_24h_quote": row.get("volume_quote"),
                            "timestamp": str(ts) if ts is not None else None,
                        }
                    )

        if not venues:
            raise HTTPException(
                status_code=404, detail=f"No market data found across any exchange for {symbol}"
            )

        # Filter out venues with non-positive prices
        valid_venues = [v for v in venues if v["last_price"] is not None and v["last_price"] > 0]
        if not valid_venues:
            raise HTTPException(status_code=404, detail=f"No valid price quotes for {symbol}")

        # Compute cross-venue arbitrage metrics
        prices = [v["last_price"] for v in valid_venues]
        min_px = min(prices)
        max_px = max(prices)
        spread_abs = max_px - min_px
        spread_bps = (spread_abs / min_px) * 10000.0 if min_px > 0 else 0.0

        best_buy_venue = min(valid_venues, key=lambda v: v["ask_price"] or v["last_price"])
        best_sell_venue = max(valid_venues, key=lambda v: v["bid_price"] or v["last_price"])

        # Check for crossed market arbitrage (bid on venue A > ask on venue B)
        best_bid = best_sell_venue.get("bid_price") or best_sell_venue["last_price"]
        best_ask = best_buy_venue.get("ask_price") or best_buy_venue["last_price"]

        is_arbitrage = bool(
            best_bid > best_ask and best_sell_venue["exchange"] != best_buy_venue["exchange"]
        )
        gross_arb_bps = ((best_bid - best_ask) / best_ask * 10000.0) if is_arbitrage else 0.0

        return {
            "symbol": symbol,
            "base": base,
            "quote": quote,
            "venue_count": len(valid_venues),
            "spread_summary": {
                "min_price": min_px,
                "max_price": max_px,
                "spread_abs": round(spread_abs, 4),
                "spread_bps": round(spread_bps, 2),
                "best_buy_venue": best_buy_venue["exchange"],
                "best_buy_price": best_ask,
                "best_sell_venue": best_sell_venue["exchange"],
                "best_sell_price": best_bid,
                "arbitrage_opportunity": is_arbitrage,
                "gross_arbitrage_bps": round(gross_arb_bps, 2),
            },
            "venues": valid_venues,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to compare prices", error=str(e), symbol=symbol)
        raise HTTPException(status_code=500, detail="Internal server error")
