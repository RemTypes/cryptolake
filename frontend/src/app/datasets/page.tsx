"use client";

import React, { useState } from "react";
import {
  Database,
  Download,
  Filter,
  FileCode,
  Table,
  CheckCircle2,
  ExternalLink,
} from "lucide-react";
import { api } from "@/lib/api";

interface DatasetRow {
  exchange: string;
  dataset: "ohlcv" | "tickers";
  symbol: string;
  interval: string;
  dates: string[];
  fileCount: number;
  estRows: number;
}

const LAKE_INVENTORY: DatasetRow[] = [
  // Binance
  { exchange: "binance", dataset: "ohlcv", symbol: "BTC-USDT", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "binance", dataset: "ohlcv", symbol: "ETH-USDT", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "binance", dataset: "ohlcv", symbol: "SOL-USDT", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "binance", dataset: "ohlcv", symbol: "BTC-USD", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "binance", dataset: "ohlcv", symbol: "ETH-USD", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "binance", dataset: "ohlcv", symbol: "SOL-USD", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "binance", dataset: "tickers", symbol: "ALL-PAIRS", interval: "snapshot", dates: ["2026-09-09", "2026-09-11"], fileCount: 2, estRows: 3701 },

  // Coinbase
  { exchange: "coinbase", dataset: "ohlcv", symbol: "BTC-USDT", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "coinbase", dataset: "ohlcv", symbol: "BTC-USD", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "coinbase", dataset: "ohlcv", symbol: "ETH-USDT", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "coinbase", dataset: "ohlcv", symbol: "ETH-USD", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "coinbase", dataset: "ohlcv", symbol: "SOL-USDT", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "coinbase", dataset: "ohlcv", symbol: "SOL-USD", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "coinbase", dataset: "tickers", symbol: "MAJOR-PAIRS", interval: "snapshot", dates: ["2026-09-11"], fileCount: 1, estRows: 5 },

  // Kraken
  { exchange: "kraken", dataset: "ohlcv", symbol: "BTC-USDT", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "kraken", dataset: "ohlcv", symbol: "BTC-USD", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "kraken", dataset: "ohlcv", symbol: "ETH-USDT", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "kraken", dataset: "ohlcv", symbol: "ETH-USD", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "kraken", dataset: "ohlcv", symbol: "SOL-USDT", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "kraken", dataset: "ohlcv", symbol: "SOL-USD", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "kraken", dataset: "tickers", symbol: "MAJOR-PAIRS", interval: "snapshot", dates: ["2026-09-11"], fileCount: 1, estRows: 5 },

  // OKX
  { exchange: "okx", dataset: "ohlcv", symbol: "BTC-USDT", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "okx", dataset: "ohlcv", symbol: "BTC-USD", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "okx", dataset: "ohlcv", symbol: "ETH-USDT", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "okx", dataset: "ohlcv", symbol: "ETH-USD", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "okx", dataset: "ohlcv", symbol: "SOL-USDT", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "okx", dataset: "ohlcv", symbol: "SOL-USD", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "okx", dataset: "tickers", symbol: "SPOT-ALL", interval: "snapshot", dates: ["2026-09-11"], fileCount: 1, estRows: 1416 },

  // Bybit
  { exchange: "bybit", dataset: "ohlcv", symbol: "BTC-USDT", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "bybit", dataset: "ohlcv", symbol: "BTC-USD", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "bybit", dataset: "ohlcv", symbol: "ETH-USDT", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "bybit", dataset: "ohlcv", symbol: "ETH-USD", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "bybit", dataset: "ohlcv", symbol: "SOL-USDT", interval: "1h", dates: ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], fileCount: 4, estRows: 72 },
  { exchange: "bybit", dataset: "tickers", symbol: "SPOT-ALL", interval: "snapshot", dates: ["2026-09-11"], fileCount: 1, estRows: 538 },
];

export default function DatasetsPage() {
  const [selectedExchange, setSelectedExchange] = useState<string>("all");
  const [selectedSymbol, setSelectedSymbol] = useState<string>("all");
  const [selectedDataset, setSelectedDataset] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const filtered = LAKE_INVENTORY.filter((item) => {
    if (selectedExchange !== "all" && item.exchange !== selectedExchange) return false;
    if (selectedDataset !== "all" && item.dataset !== selectedDataset) return false;
    if (selectedSymbol !== "all" && !item.symbol.includes(selectedSymbol)) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        item.exchange.toLowerCase().includes(q) ||
        item.symbol.toLowerCase().includes(q) ||
        item.dataset.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-terminal-border pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white font-mono flex items-center gap-2">
            <Database className="w-6 h-6 text-cyan-400" />
            <span>Parquet Data Lake Catalog</span>
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Browse and download partitioned Apache Parquet files generated from exchange ingestion.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <span className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-cyan-400 font-semibold">
            {filtered.length} Partitions Shown
          </span>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 bg-terminal-card border border-terminal-border rounded-xl p-4 font-mono text-xs">
        <div>
          <label className="text-slate-500 block mb-1.5 font-medium">Filter Venue</label>
          <select
            value={selectedExchange}
            onChange={(e) => setSelectedExchange(e.target.value)}
            className="w-full bg-slate-900 border border-terminal-border rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="all">All Venues (5)</option>
            <option value="binance">Binance</option>
            <option value="coinbase">Coinbase</option>
            <option value="kraken">Kraken</option>
            <option value="okx">OKX</option>
            <option value="bybit">Bybit</option>
          </select>
        </div>

        <div>
          <label className="text-slate-500 block mb-1.5 font-medium">Filter Asset</label>
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="w-full bg-slate-900 border border-terminal-border rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="all">All Assets</option>
            <option value="BTC">Bitcoin (BTC)</option>
            <option value="ETH">Ethereum (ETH)</option>
            <option value="SOL">Solana (SOL)</option>
          </select>
        </div>

        <div>
          <label className="text-slate-500 block mb-1.5 font-medium">Dataset Type</label>
          <select
            value={selectedDataset}
            onChange={(e) => setSelectedDataset(e.target.value)}
            className="w-full bg-slate-900 border border-terminal-border rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="all">All Datasets</option>
            <option value="ohlcv">OHLCV Candlesticks</option>
            <option value="tickers">24h Tickers</option>
          </select>
        </div>

        <div>
          <label className="text-slate-500 block mb-1.5 font-medium">Search Partitions</label>
          <input
            type="text"
            placeholder="Search e.g. BTC-USDT..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900 border border-terminal-border rounded-lg px-3 py-2 text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      {/* Dataset Table */}
      <div className="bg-terminal-card border border-terminal-border rounded-xl overflow-hidden shadow-lg font-mono text-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-terminal-border bg-slate-900/60 text-slate-400 text-[11px] uppercase tracking-wider">
                <th className="py-3 px-4">Dataset</th>
                <th className="py-3 px-4">Exchange</th>
                <th className="py-3 px-4">Symbol / Pair</th>
                <th className="py-3 px-4">Interval</th>
                <th className="py-3 px-4">Files & Partitions</th>
                <th className="py-3 px-4">Est. Rows</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-terminal-border/60">
              {filtered.map((row, idx) => {
                const downloadParquetUrl = api.getDownloadUrl(
                  row.exchange,
                  row.symbol,
                  row.interval,
                  "parquet"
                );
                const downloadCsvUrl = api.getDownloadUrl(
                  row.exchange,
                  row.symbol,
                  row.interval,
                  "csv"
                );

                return (
                  <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                          row.dataset === "ohlcv"
                            ? "bg-cyan-950 text-cyan-400 border border-cyan-800/60"
                            : "bg-purple-950 text-purple-400 border border-purple-800/60"
                        }`}
                      >
                        {row.dataset}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-200 uppercase">
                      {row.exchange}
                    </td>
                    <td className="py-3 px-4 font-medium text-white">{row.symbol}</td>
                    <td className="py-3 px-4 text-slate-400">{row.interval}</td>
                    <td className="py-3 px-4 text-slate-300">
                      <span className="text-cyan-400 font-semibold">{row.fileCount} files</span>{" "}
                      <span className="text-slate-500 text-[10px]">
                        ({row.dates[0]} → {row.dates[row.dates.length - 1]})
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-300">{row.estRows.toLocaleString()}</td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <a
                          href={downloadParquetUrl}
                          download
                          title="Download Parquet File"
                          className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-cyan-600 text-slate-300 hover:text-white border border-slate-700 transition-colors"
                        >
                          <Download className="w-3 h-3 text-cyan-400 hover:text-white" />
                          <span>Parquet</span>
                        </a>
                        <a
                          href={downloadCsvUrl}
                          download
                          title="Download CSV"
                          className="flex items-center gap-1 px-2 py-1 rounded bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 transition-colors"
                        >
                          <span>CSV</span>
                        </a>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Code Snippet: Querying via Python */}
      <div className="bg-terminal-card border border-terminal-border rounded-xl p-5 space-y-3 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-terminal-border pb-2.5">
          <div className="flex items-center gap-2">
            <FileCode className="w-4 h-4 text-cyan-400" />
            <h3 className="font-bold text-white">Direct Polars / PyArrow Python Access</h3>
          </div>
          <span className="text-slate-500 text-[11px]">Zero Copy In-Memory</span>
        </div>
        <p className="text-slate-400">
          Because the lake stores standard Apache Parquet with Snappy compression, you can read partitions directly without going through HTTP:
        </p>
        <pre className="p-4 rounded-lg bg-slate-950 border border-terminal-border text-slate-300 overflow-x-auto text-[11px] leading-relaxed">
{`import polars as pl

# 1. Scan partitioned Parquet files with predicate pushdown:
df = pl.scan_parquet("data/ohlcv/binance/BTC-USDT/1h/*.parquet") \\
       .filter(pl.col("close") > 75000) \\
       .collect()

print(df.head())`}
        </pre>
      </div>
    </div>
  );
}
