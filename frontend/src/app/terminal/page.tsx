"use client";

import React, { useEffect, useState } from "react";
import { CandlestickChart } from "@/components/CandlestickChart";
import { api, type OHLCVCandle, type CompareResult } from "@/lib/api";
import { formatCurrency, formatBps } from "@/lib/utils";
import {
  LineChart,
  RefreshCw,
  Zap,
  TrendingUp,
  AlertCircle,
  Share2,
} from "lucide-react";

export default function TerminalPage() {
  const [symbol, setSymbol] = useState<string>("BTC-USDT");
  const [exchange, setExchange] = useState<string>("binance");
  const [candles, setCandles] = useState<OHLCVCandle[]>([]);
  const [compare, setCompare] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [candleData, compareData] = await Promise.allSettled([
        api.getOHLCV(exchange, symbol, "1h"),
        api.getCompare(symbol),
      ]);

      if (candleData.status === "fulfilled") {
        setCandles(candleData.value);
      } else {
        setError(`Could not load candles for ${exchange} ${symbol}`);
      }

      if (compareData.status === "fulfilled") {
        setCompare(compareData.value);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load market data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [symbol, exchange]);

  return (
    <div className="space-y-6">
      {/* Top Header & Venue Selectors */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-terminal-border pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white font-mono flex items-center gap-2">
            <LineChart className="w-6 h-6 text-emerald-400" />
            <span>Market Microstructure Terminal</span>
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-1">
            TradingView Lightweight Charts integrated with multi-exchange order book spreads.
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-3 font-mono text-xs">
          <div>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="bg-terminal-card border border-terminal-border rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500 font-semibold"
            >
              <option value="BTC-USDT">BTC-USDT</option>
              <option value="ETH-USDT">ETH-USDT</option>
              <option value="SOL-USDT">SOL-USDT</option>
              <option value="BTC-USD">BTC-USD</option>
              <option value="ETH-USD">ETH-USD</option>
            </select>
          </div>

          <div>
            <select
              value={exchange}
              onChange={(e) => setExchange(e.target.value)}
              className="bg-terminal-card border border-terminal-border rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500 font-semibold uppercase"
            >
              <option value="binance">Binance</option>
              <option value="coinbase">Coinbase</option>
              <option value="kraken">Kraken</option>
              <option value="okx">OKX</option>
              <option value="bybit">Bybit</option>
            </select>
          </div>

          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-cyan-400" : ""}`} />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-mono">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Candlestick Chart */}
      <CandlestickChart
        candles={candles}
        symbol={symbol}
        exchange={exchange}
      />

      {/* Cross-Exchange Arbitrage & Spread Analysis */}
      {compare && (
        <div className="bg-terminal-card border border-terminal-border rounded-xl p-5 space-y-4 font-mono">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-terminal-border pb-3">
            <div>
              <div className="flex items-center gap-2">
                <Share2 className="w-4 h-4 text-cyan-400" />
                <h2 className="text-sm font-bold text-white tracking-tight">
                  Cross-Venue Price & Arbitrage Matrix ({compare.symbol})
                </h2>
                <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-semibold">
                  {compare.venue_count} Exchanges Active
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Calculates global lowest ask vs highest bid across independent order books.
              </p>
            </div>

            {/* Arbitrage Badge */}
            {compare.spread_summary.arbitrage_opportunity ? (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
                <Zap className="w-4 h-4 text-emerald-400" />
                <span>
                  Gross Arbitrage: {formatBps(compare.spread_summary.gross_arbitrage_bps)}
                </span>
              </div>
            ) : (
              <div className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-400 text-xs">
                No active arbitrage opportunity
              </div>
            )}
          </div>

          {/* Arbitrage Summary Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block">Best Buy Venue (Lowest Ask)</span>
              <span className="text-emerald-400 font-bold uppercase block mt-1">
                {compare.spread_summary.best_buy_venue || "—"}
              </span>
              <span className="text-slate-300">
                {formatCurrency(compare.spread_summary.best_buy_price)}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block">Best Sell Venue (Highest Bid)</span>
              <span className="text-rose-400 font-bold uppercase block mt-1">
                {compare.spread_summary.best_sell_venue || "—"}
              </span>
              <span className="text-slate-300">
                {formatCurrency(compare.spread_summary.best_sell_price)}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block">Cross-Venue Spread</span>
              <span className="text-white font-bold block mt-1">
                {formatCurrency(compare.spread_summary.spread_abs)}
              </span>
              <span className="text-slate-400">
                {formatBps(compare.spread_summary.spread_bps)}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block">Price Range (Min → Max)</span>
              <span className="text-white font-bold block mt-1">
                {formatCurrency(compare.spread_summary.min_price)}
              </span>
              <span className="text-slate-400">
                → {formatCurrency(compare.spread_summary.max_price)}
              </span>
            </div>
          </div>

          {/* Venue Table */}
          <div className="overflow-x-auto pt-2">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="text-slate-500 border-b border-slate-800/80 uppercase text-[10px]">
                  <th className="py-2.5 px-3">Exchange</th>
                  <th className="py-2.5 px-3">Last Trade</th>
                  <th className="py-2.5 px-3">Best Bid</th>
                  <th className="py-2.5 px-3">Best Ask</th>
                  <th className="py-2.5 px-3">Venue Spread</th>
                  <th className="py-2.5 px-3">24h Quote Turnover</th>
                  <th className="py-2.5 px-3 text-right">Data Freshness</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {compare.venues.map((v) => {
                  const isBestBuy = v.exchange === compare.spread_summary.best_buy_venue;
                  const isBestSell = v.exchange === compare.spread_summary.best_sell_venue;

                  return (
                    <tr
                      key={v.exchange}
                      className={`hover:bg-slate-800/30 transition-colors ${
                        isBestBuy ? "bg-emerald-950/20" : isBestSell ? "bg-rose-950/20" : ""
                      }`}
                    >
                      <td className="py-2.5 px-3 font-semibold uppercase text-slate-200 flex items-center gap-2">
                        <span>{v.exchange}</span>
                        {isBestBuy && (
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/40">
                            CHEAPEST BUY
                          </span>
                        )}
                        {isBestSell && (
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-400 font-bold border border-rose-500/40">
                            RICHEST SELL
                          </span>
                        )}
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
                      <td className="py-2.5 px-3 text-right text-slate-500 text-[10px]">
                        {v.timestamp ? new Date(v.timestamp).toLocaleTimeString() : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

