"use client";

import React, { useEffect, useState } from "react";
import { api, type CompareResult } from "@/lib/api";
import { formatCurrency, formatBps } from "@/lib/utils";
import { ArrowUpRight, CheckCircle2, RefreshCw, Zap } from "lucide-react";

export const LakeStatsHeader: React.FC = () => {
  const [btcCompare, setBtcCompare] = useState<CompareResult | null>(null);
  const [ethCompare, setEthCompare] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  const fetchData = async () => {
    setLoading(true);
    try {
      const [btc, eth] = await Promise.allSettled([
        api.getCompare("BTC-USDT"),
        api.getCompare("ETH-USDT"),
      ]);
      if (btc.status === "fulfilled") setBtcCompare(btc.value);
      if (eth.status === "fulfilled") setEthCompare(eth.value);
      setLastRefreshed(new Date());
    } catch (err) {
      console.error("Failed to fetch compare data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Auto-poll every 15s
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="border-b border-terminal-border bg-terminal-card/60 px-4 lg:px-8 py-2.5">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
        {/* Metric Badges */}
        <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="text-slate-500">Venues:</span>
            <span className="text-slate-200 font-semibold flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              5 Active
            </span>
            <span className="text-slate-600 text-[10px]">(Binance, Coinbase, Kraken, OKX, Bybit)</span>
          </div>

          <div className="hidden sm:flex items-center gap-2 pl-3 border-l border-terminal-border">
            <span className="text-slate-500">Parquet Files:</span>
            <span className="text-cyan-400 font-semibold">122 Partitions</span>
          </div>

          <div className="hidden md:flex items-center gap-2 pl-3 border-l border-terminal-border">
            <span className="text-slate-500">Historical Depth:</span>
            <span className="text-slate-300 font-medium">3 Days (Hourly)</span>
          </div>
        </div>

        {/* Live Ticker Spreads */}
        <div className="flex items-center gap-3">
          {btcCompare && (
            <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-xs font-mono">
              <span className="font-bold text-amber-400">BTC</span>
              <span className="text-slate-200">
                {formatCurrency(btcCompare.spread_summary.min_price)}
              </span>
              <span
                className={`text-[10px] px-1 rounded ${
                  btcCompare.spread_summary.arbitrage_opportunity
                    ? "bg-emerald-500/20 text-emerald-400 font-semibold"
                    : "text-slate-500"
                }`}
              >
                Arb {formatBps(btcCompare.spread_summary.gross_arbitrage_bps)}
              </span>
            </div>
          )}

          {ethCompare && (
            <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-xs font-mono">
              <span className="font-bold text-indigo-400">ETH</span>
              <span className="text-slate-200">
                {formatCurrency(ethCompare.spread_summary.min_price)}
              </span>
              <span
                className={`text-[10px] px-1 rounded ${
                  ethCompare.spread_summary.arbitrage_opportunity
                    ? "bg-emerald-500/20 text-emerald-400 font-semibold"
                    : "text-slate-500"
                }`}
              >
                Arb {formatBps(ethCompare.spread_summary.gross_arbitrage_bps)}
              </span>
            </div>
          )}

          <button
            onClick={fetchData}
            title="Refresh lake tickers"
            className="p-1 rounded text-slate-500 hover:text-cyan-400 hover:bg-slate-800 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-cyan-400" : ""}`} />
          </button>
        </div>
      </div>
    </div>
  );
};
