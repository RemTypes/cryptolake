"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Database,
  LineChart,
  Atom,
  BookOpen,
  ArrowRight,
  ShieldCheck,
  TrendingUp,
  Cpu,
  Share2,
  Sparkles,
} from "lucide-react";
import { api, type CompareResult } from "@/lib/api";
import { formatCurrency, formatBps } from "@/lib/utils";

export default function OverviewPage() {
  const [btcCompare, setBtcCompare] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getCompare("BTC-USDT")
      .then(setBtcCompare)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl border border-terminal-border bg-gradient-to-b from-slate-900/90 to-terminal-card/80 p-6 lg:p-10">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-mono">
            <Sparkles className="w-3.5 h-3.5" />
            <span>King's College London — Mathematical Research Portfolio</span>
          </div>
          <h1 className="text-3xl lg:text-5xl font-bold tracking-tight text-white font-mono">
            High-Performance Crypto Data Lake & <span className="text-cyan-400">Quantitative Lab</span>
          </h1>
          <p className="text-slate-400 text-sm lg:text-base leading-relaxed">
            Ingests tick and OHLCV market data across 5 major exchanges into unified, partitioned
            Apache Parquet files. Explores pure mathematics in market microstructure: Topological
            Data Analysis (TDA), Riemannian metric spaces, and heavy-tailed distribution dynamics.
          </p>
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link
              href="/math-lab"
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-semibold shadow-lg shadow-cyan-600/25 transition-all"
            >
              <Atom className="w-4 h-4" />
              <span>Explore Math Lab</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/datasets"
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-200 border border-slate-700 font-mono text-xs font-semibold transition-all"
            >
              <Database className="w-4 h-4 text-cyan-400" />
              <span>Browse Parquet Lake</span>
            </Link>
          </div>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
        <div className="bg-terminal-card border border-terminal-border rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Parquet Partitions</span>
            <Database className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-white tracking-tight">122 Files</div>
          <p className="text-[11px] text-slate-500">Partitioned by Venue, Pair & Date</p>
        </div>

        <div className="bg-terminal-card border border-terminal-border rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Connected Venues</span>
            <Cpu className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 tracking-tight">5 Exchanges</div>
          <p className="text-[11px] text-slate-500">Binance, Coinbase, Kraken, OKX, Bybit</p>
        </div>

        <div className="bg-terminal-card border border-terminal-border rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Historical Depth</span>
            <TrendingUp className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-white tracking-tight">3 Days</div>
          <p className="text-[11px] text-slate-500">2,106 OHLCV + 5,665 Ticker Rows</p>
        </div>

        <div className="bg-terminal-card border border-terminal-border rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Active Arbitrage</span>
            <Share2 className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-purple-400 tracking-tight">
            {btcCompare ? formatBps(btcCompare.spread_summary.gross_arbitrage_bps) : "Scanning..."}
          </div>
          <p className="text-[11px] text-slate-500">
            {btcCompare?.spread_summary.best_buy_venue
              ? `Buy ${btcCompare.spread_summary.best_buy_venue.toUpperCase()} → Sell ${btcCompare.spread_summary.best_sell_venue.toUpperCase()}`
              : "Cross-exchange spread delta"}
          </p>
        </div>
      </div>

      {/* Main Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card 1: Math Lab */}
        <Link
          href="/math-lab"
          className="group bg-terminal-card border border-terminal-border hover:border-cyan-500/50 rounded-xl p-6 space-y-4 transition-all hover:shadow-xl hover:shadow-cyan-500/5"
        >
          <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 group-hover:scale-110 transition-transform">
            <Atom className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white font-mono group-hover:text-cyan-400 transition-colors">
              Quantitative Math Lab
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Interactive 3D phase space embeddings, correlation manifolds, and heavy-tail analysis
              grounded in BSc pure mathematics.
            </p>
          </div>
          <div className="text-xs font-mono text-cyan-400 flex items-center gap-1 font-medium">
            <span>Open Lab Modules</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>

        {/* Card 2: Terminal */}
        <Link
          href="/terminal"
          className="group bg-terminal-card border border-terminal-border hover:border-emerald-500/50 rounded-xl p-6 space-y-4 transition-all hover:shadow-xl hover:shadow-emerald-500/5"
        >
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 group-hover:scale-110 transition-transform">
            <LineChart className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white font-mono group-hover:text-emerald-400 transition-colors">
              Market Terminal & Spreads
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Interactive TradingView candlesticks with volume histograms and real-time
              cross-venue order book arbitrage matrices.
            </p>
          </div>
          <div className="text-xs font-mono text-emerald-400 flex items-center gap-1 font-medium">
            <span>View Candlesticks</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>

        {/* Card 3: Datasets */}
        <Link
          href="/datasets"
          className="group bg-terminal-card border border-terminal-border hover:border-purple-500/50 rounded-xl p-6 space-y-4 transition-all hover:shadow-xl hover:shadow-purple-500/5"
        >
          <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 group-hover:scale-110 transition-transform">
            <Database className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white font-mono group-hover:text-purple-400 transition-colors">
              Parquet Lake Catalog
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Inspect partition schemas, preview row samples, and download partitioned datasets
              in Apache Parquet or CSV format.
            </p>
          </div>
          <div className="text-xs font-mono text-purple-400 flex items-center gap-1 font-medium">
            <span>Browse Datasets</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>
      </div>

      {/* Live Venue Arbitrage Matrix Snapshot */}
      {btcCompare && (
        <div className="bg-terminal-card border border-terminal-border rounded-xl p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-terminal-border pb-3">
            <div>
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <span>BTC-USDT Cross-Venue Price Snapshot</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  {btcCompare.venue_count} Venues Connected
                </span>
              </h3>
              <p className="text-xs text-slate-400 font-mono">
                Live order book quotes and basis point spread from the data lake
              </p>
            </div>
            <Link
              href="/terminal"
              className="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
            >
              <span>Detailed Comparison</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs font-mono text-left">
              <thead>
                <tr className="text-slate-500 border-b border-slate-800/80">
                  <th className="py-2 px-3">Exchange</th>
                  <th className="py-2 px-3">Last Price</th>
                  <th className="py-2 px-3">Best Bid</th>
                  <th className="py-2 px-3">Best Ask</th>
                  <th className="py-2 px-3">Venue Spread</th>
                  <th className="py-2 px-3">24h Quote Vol</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {btcCompare.venues.map((v) => (
                  <tr key={v.exchange} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-2.5 px-3 font-semibold text-slate-200 uppercase">
                      {v.exchange}
                    </td>
                    <td className="py-2.5 px-3 text-slate-100">{formatCurrency(v.last_price)}</td>
                    <td className="py-2.5 px-3 text-emerald-400">{formatCurrency(v.bid_price)}</td>
                    <td className="py-2.5 px-3 text-rose-400">{formatCurrency(v.ask_price)}</td>
                    <td className="py-2.5 px-3 text-slate-400">
                      {v.ask_price && v.bid_price
                        ? formatBps(((v.ask_price - v.bid_price) / v.ask_price) * 10000)
                        : "—"}
                    </td>
                    <td className="py-2.5 px-3 text-slate-400">
                      {formatCurrency(v.volume_24h_quote, 0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
