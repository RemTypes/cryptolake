"use client";

import React, { useState } from "react";
import { 
  BookOpen, 
  Code2, 
  Copy, 
  Check, 
  Terminal, 
  Database, 
  Cpu, 
  ExternalLink,
  ChevronRight,
  Sparkles,
  Layers,
  Search
} from "lucide-react";
import { KaTeX } from "@/components/KaTeX";

interface EndpointDoc {
  method: "GET" | "POST";
  path: string;
  category: "Data Lake" | "Math Research" | "System";
  summary: string;
  description: string;
  params: { name: string; type: string; required: boolean; defaultVal?: string; desc: string }[];
  mathConcept?: string;
  sampleCurl: string;
  samplePython: string;
  responsePreview: string;
}

const ENDPOINTS: EndpointDoc[] = [
  {
    method: "GET",
    path: "/api/v1/stats",
    category: "System",
    summary: "Data lake aggregation metrics",
    description: "Returns partition statistics, total storage size, row counts, and date bounds across all ingested exchanges.",
    params: [],
    sampleCurl: "curl -s http://127.0.0.1:8000/api/v1/stats | jq .",
    samplePython: `import httpx

res = httpx.get("http://127.0.0.1:8000/api/v1/stats")
data = res.json()
print(f"Total Rows: {data['total_rows']:,} | Total Files: {data['total_files']}")`,
    responsePreview: `{
  "total_files": 122,
  "total_size_mb": 0.48,
  "total_rows": 7771,
  "exchanges": ["binance", "bybit", "coinbase", "kraken", "okx"],
  "symbols": ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BTC/USD"],
  "date_range": { "min": "2026-09-08", "max": "2026-09-11" }
}`,
  },
  {
    method: "GET",
    path: "/api/v1/ohlcv",
    category: "Data Lake",
    summary: "Query historical OHLCV candles",
    description: "High-performance candle retrieval filtered across partitions. Supports JSON records or streaming raw binary Parquet.",
    params: [
      { name: "symbol", type: "string", required: true, defaultVal: "BTC/USDT", desc: "Base/quote trading pair" },
      { name: "exchange", type: "string", required: false, defaultVal: "binance", desc: "Source exchange filter" },
      { name: "interval", type: "string", required: false, defaultVal: "1h", desc: "Candle granularity (1m, 5m, 1h, 1d)" },
      { name: "start_time", type: "string", required: false, desc: "ISO-8601 timestamp cutoff" },
      { name: "end_time", type: "string", required: false, desc: "ISO-8601 timestamp cutoff" },
      { name: "format", type: "string", required: false, defaultVal: "json", desc: "'json' or 'parquet'" },
    ],
    sampleCurl: "curl -s 'http://127.0.0.1:8000/api/v1/ohlcv?symbol=BTC/USDT&interval=1h&limit=10' | jq .",
    samplePython: `import polars as pl

# Direct Polars lazy scan on parquet partitions
df = pl.scan_parquet("data/ohlcv/exchange=binance/interval=1h/**/*.parquet") \\
       .filter(pl.col("symbol") == "BTC/USDT") \\
       .sort("timestamp") \\
       .collect()
print(df.tail(5))`,
    responsePreview: `[
  {
    "timestamp": 1725840000000,
    "symbol": "BTC/USDT",
    "exchange": "binance",
    "open": 54320.10,
    "high": 54890.00,
    "low": 54100.50,
    "close": 54720.00,
    "volume": 1248.52
  }
]`,
  },
  {
    method: "GET",
    path: "/api/v1/math/tda/takens",
    category: "Math Research",
    summary: "Takens phase-space delay reconstruction & entropy",
    description: "Reconstructs the dynamical attractor manifold in R^3 via Takens' Delay Embedding Theorem and computes sliding Shannon persistence entropy.",
    mathConcept: "\\Phi(x_t) = (x_t, x_{t-\\tau}, x_{t-2\\tau}) \\in \\mathbb{R}^3",
    params: [
      { name: "symbol", type: "string", required: false, defaultVal: "BTC/USDT", desc: "Target asset time series" },
      { name: "exchange", type: "string", required: false, defaultVal: "binance", desc: "Exchange source" },
      { name: "interval", type: "string", required: false, defaultVal: "1h", desc: "Granularity" },
      { name: "delay", type: "integer", required: false, defaultVal: "1", desc: "Time lag tau" },
      { name: "dim", type: "integer", required: false, defaultVal: "3", desc: "Embedding dimension m" },
      { name: "window_size", type: "integer", required: false, defaultVal: "24", desc: "Sliding window for entropy" },
    ],
    sampleCurl: "curl -s 'http://127.0.0.1:8000/api/v1/math/tda/takens?symbol=BTC/USDT&delay=2' | jq .",
    samplePython: `import httpx

res = httpx.get("http://127.0.0.1:8000/api/v1/math/tda/takens", params={
    "symbol": "BTC/USDT",
    "delay": 1,
    "dim": 3,
    "window_size": 24
})
data = res.json()
print("Trajectories:", len(data["trajectory"]))
print("Current Entropy:", data["entropy_series"][-1]["entropy"])`,
    responsePreview: `{
  "symbol": "BTC/USDT",
  "delay": 1,
  "dim": 3,
  "n_points": 72,
  "trajectory": [
    { "t": 1725840000000, "x": 54720.0, "y": 54310.2, "z": 53980.5 }
  ],
  "entropy_series": [
    { "t": 1725926400000, "entropy": 2.451 }
  ]
}`,
  },
  {
    method: "GET",
    path: "/api/v1/math/geometry/correlation",
    category: "Math Research",
    summary: "Riemannian distance & classical MDS coordinates",
    description: "Transforms empirical correlation coefficients rho_ij into an ultrametric Riemannian distance d_ij = sqrt(2(1 - rho_ij)) and projects to 2D/3D via eigendecomposition.",
    mathConcept: "d_{ij} = \\sqrt{2(1 - \\rho_{ij})}, \\quad B = -\\frac{1}{2} H D^2 H = V \\Lambda V^T",
    params: [
      { name: "symbols", type: "string", required: false, defaultVal: "BTC/USDT,ETH/USDT,SOL/USDT", desc: "Comma-separated asset universe" },
      { name: "exchange", type: "string", required: false, defaultVal: "binance", desc: "Exchange benchmark" },
      { name: "interval", type: "string", required: false, defaultVal: "1h", desc: "Return series frequency" },
      { name: "window_days", type: "integer", required: false, defaultVal: "3", desc: "Historical lookback in days" },
    ],
    sampleCurl: "curl -s 'http://127.0.0.1:8000/api/v1/math/geometry/correlation' | jq .",
    samplePython: `import httpx
import numpy as np

res = httpx.get("http://127.0.0.1:8000/api/v1/math/geometry/correlation")
payload = res.json()
print("Assets:", payload["symbols"])
coords = {pt["symbol"]: (pt["x"], pt["y"]) for pt in payload["coordinates_2d"]}
print("2D MDS Embeddings:", coords)`,
    responsePreview: `{
  "symbols": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
  "correlation_matrix": [
    [1.0, 0.884, 0.762],
    [0.884, 1.0, 0.819],
    [0.762, 0.819, 1.0]
  ],
  "distance_matrix": [
    [0.0, 0.481, 0.690],
    [0.481, 0.0, 0.602],
    [0.690, 0.602, 0.0]
  ],
  "coordinates_2d": [
    { "symbol": "BTC/USDT", "x": 0.312, "y": -0.054 },
    { "symbol": "ETH/USDT", "x": -0.045, "y": 0.281 },
    { "symbol": "SOL/USDT", "x": -0.267, "y": -0.227 }
  ],
  "explained_variance_ratio": [0.684, 0.316]
}`,
  },
  {
    method: "GET",
    path: "/api/v1/math/stats/distribution",
    category: "Math Research",
    summary: "Parametric fat-tail fitting & normality hypothesis tests",
    description: "Computes empirical log-returns, excess kurtosis, skewness, fits a Student-t distribution via MLE, and evaluates Jarque-Bera tests.",
    mathConcept: "r_t = \\ln\\left(\\frac{P_t}{P_{t-1}}\\right), \\quad f(r; \\nu) = \\frac{\\Gamma\\left(\\frac{\\nu+1}{2}\\right)}{\\sqrt{\\pi \\nu}\\Gamma\\left(\\frac{\\nu}{2}\\right)}\\left(1 + \\frac{r^2}{\\nu}\\right)^{-\\frac{\\nu+1}{2}}",
    params: [
      { name: "symbol", type: "string", required: false, defaultVal: "BTC/USDT", desc: "Asset symbol" },
      { name: "exchange", type: "string", required: false, defaultVal: "binance", desc: "Exchange source" },
      { name: "interval", type: "string", required: false, defaultVal: "1h", desc: "Return series frequency" },
    ],
    sampleCurl: "curl -s 'http://127.0.0.1:8000/api/v1/math/stats/distribution?symbol=ETH/USDT' | jq .",
    samplePython: `from scipy import stats
import httpx

res = httpx.get("http://127.0.0.1:8000/api/v1/math/stats/distribution", params={"symbol": "ETH/USDT"})
dist = res.json()
print(f"Degrees of Freedom (nu): {dist['student_t']['df']:.2f}")
print(f"Excess Kurtosis: {dist['empirical']['kurtosis']:.2f}")
print(f"Jarque-Bera p-value: {dist['jarque_bera']['p_value']:.4e}")`,
    responsePreview: `{
  "symbol": "ETH/USDT",
  "empirical": {
    "mean": 0.00014,
    "variance": 0.00012,
    "skewness": -0.42,
    "kurtosis": 4.88
  },
  "student_t": {
    "df": 3.42,
    "loc": 0.00011,
    "scale": 0.0084
  },
  "jarque_bera": {
    "statistic": 48.91,
    "p_value": 2.39e-11,
    "reject_gaussian_at_5pct": true
  }
}`,
  },
  {
    method: "GET",
    path: "/api/v1/math/microstructure/spreads",
    category: "Math Research",
    summary: "Multi-exchange orderbook bid-ask spreads & arbitrage",
    description: "Evaluates cross-venue price dispersion, instant cross-exchange arbitrage basis points, and relative effective spreads from concurrent ticker snapshots.",
    params: [
      { name: "symbol", type: "string", required: false, defaultVal: "BTC/USDT", desc: "Target quote currency pair" },
    ],
    sampleCurl: "curl -s 'http://127.0.0.1:8000/api/v1/math/microstructure/spreads?symbol=BTC/USDT' | jq .",
    samplePython: `import httpx

res = httpx.get("http://127.0.0.1:8000/api/v1/math/microstructure/spreads", params={"symbol": "BTC/USDT"})
arb = res.json()
print("Max Arbitrage Spread (bps):", arb["arbitrage"]["spread_bps"])
print(f"Buy on {arb['arbitrage']['buy_venue']} -> Sell on {arb['arbitrage']['sell_venue']}")`,
    responsePreview: `{
  "symbol": "BTC/USDT",
  "venues": {
    "binance": { "bid": 54910.10, "ask": 54910.50, "spread_bps": 0.07 },
    "okx": { "bid": 54912.00, "ask": 54912.40, "spread_bps": 0.07 }
  },
  "arbitrage": {
    "buy_venue": "binance",
    "sell_venue": "okx",
    "spread_bps": 2.73,
    "profitable_pre_fees": true
  }
}`,
  }
];

const KCL_READINGS = [
  {
    module: "Geometry of Surfaces & Metric Spaces",
    kclCode: "5CCM221A / 6CCM327A",
    title: "Hierarchical Structure in Financial Markets",
    authors: "R. N. Mantegna",
    year: 1999,
    venue: "The European Physical Journal B, 11(1), 193-197",
    link: "https://doi.org/10.1007/s100510050929",
    annotation: "Introduced the Riemannian distance metric d_ij = sqrt(2(1 - rho_ij)) on cross-correlation matrices. Proved that this metric satisfies the triangle inequality and embeds equity portfolios into an ultrametric space yielding minimum spanning trees (MSTs) and hierarchical taxonomy.",
    relevantTopics: ["Metric Spaces", "Ultrametric Distances", "Multidimensional Scaling", "Spectral Graph Theory"]
  },
  {
    module: "Applied Probability & Stochastic Analysis",
    kclCode: "5CCM241A / 6CCM342A",
    title: "The Variation of Certain Speculative Prices",
    authors: "Benoit Mandelbrot",
    year: 1963,
    venue: "The Journal of Business, 36(4), 394-419",
    link: "https://doi.org/10.1086/294632",
    annotation: "Foundational refutation of Bachelier's and Samuelson's Brownian motion models. Demonstrates that asset returns follow heavy-tailed Pareto-Levy stable distributions with infinite variance or high excess kurtosis, directly motivating Student-t and alpha-stable market representations.",
    relevantTopics: ["Fat Tails", "Heavy-Tailed Distributions", "Stable Paretian Laws", "Infinite Variance"]
  },
  {
    module: "Dynamical Systems & Topology",
    kclCode: "5CCM232A / 6CCM338A",
    title: "Detecting Strange Attractors in Turbulence",
    authors: "Floris Takens",
    year: 1981,
    venue: "Lecture Notes in Mathematics, vol 898. Springer, Berlin, Heidelberg",
    link: "https://doi.org/10.1007/BFb0091924",
    annotation: "Proves that a single observable scalar time series can reconstruct a smooth embedding of a d-dimensional compact manifold M into R^(2d+1) preserving differential and topological invariants (Lyapunov exponents, Betti numbers, homology groups).",
    relevantTopics: ["Topological Data Analysis", "Attractor Reconstruction", "Whitney Embedding Theorem", "Phase Space"]
  },
  {
    module: "Statistics 2 & Econometric Theory",
    kclCode: "5CCM242B",
    title: "Empirical Properties of Asset Returns: Stylized Facts and Statistical Issues",
    authors: "Rama Cont",
    year: 2001,
    venue: "Quantitative Finance, 1(2), 223-236",
    link: "https://doi.org/10.1080/713665670",
    annotation: "Rigorous taxonomy of the 11 universal empirical stylized facts of financial returns: absence of autocorrelations, heavy tails, gain/loss asymmetry, aggregational Gaussianity, volatility clustering, and conditional heavy tails.",
    relevantTopics: ["Maximum Likelihood Estimation", "Jarque-Bera Test", "Kurtosis & Skewness", "Quantile-Quantile Analysis"]
  },
];

export default function DocsPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [activeTab, setActiveTab] = useState<"api" | "polars" | "kcl">("api");
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const filteredEndpoints = selectedCategory === "All"
    ? ENDPOINTS
    : ENDPOINTS.filter(e => e.category === selectedCategory);

  return (
    <div className="space-y-10 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-emerald-400 mb-2">
          <BookOpen className="w-4 h-4" />
          <span>Research & Engineering Reference</span>
        </div>
        <h1 className="text-3xl font-mono font-bold text-white tracking-tight">
          System Docs & Mathematical Foundations
        </h1>
        <p className="text-zinc-400 text-sm mt-2 max-w-3xl leading-relaxed">
          Interactive developer reference for the CryptoLake API, local out-of-core Polars querying patterns, and the pure mathematical bibliography aligned with 2nd-year KCL BSc Mathematics modules.
        </p>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-zinc-800 gap-6">
        <button
          onClick={() => setActiveTab("api")}
          className={`pb-3 text-sm font-mono flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "api"
              ? "border-emerald-500 text-emerald-400 font-semibold"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <Terminal className="w-4 h-4" />
          <span>REST & Math API Explorer</span>
        </button>
        <button
          onClick={() => setActiveTab("polars")}
          className={`pb-3 text-sm font-mono flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "polars"
              ? "border-cyan-500 text-cyan-400 font-semibold"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <Cpu className="w-4 h-4" />
          <span>Polars In-Lake Query Guide</span>
        </button>
        <button
          onClick={() => setActiveTab("kcl")}
          className={`pb-3 text-sm font-mono flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "kcl"
              ? "border-purple-500 text-purple-400 font-semibold"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>KCL Math Syllabus & Bibliography</span>
        </button>
      </div>

      {/* TAB 1: API Explorer */}
      {activeTab === "api" && (
        <div className="space-y-6">
          {/* Category Filter Pills */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-zinc-500 mr-2">Filter by Group:</span>
            {["All", "Math Research", "Data Lake", "System"].map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
                  selectedCategory === cat
                    ? "bg-zinc-800 text-white border border-zinc-700 shadow-sm"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Endpoint Cards */}
          <div className="space-y-6">
            {filteredEndpoints.map((ep, idx) => (
              <div 
                key={idx} 
                className="bg-zinc-900/60 border border-zinc-800 rounded-lg overflow-hidden shadow-lg transition-all hover:border-zinc-700"
              >
                {/* Header Banner */}
                <div className="px-5 py-4 border-b border-zinc-800/80 bg-zinc-900/90 flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      {ep.method}
                    </span>
                    <span className="font-mono text-sm font-semibold text-zinc-100">
                      {ep.path}
                    </span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700/60">
                      {ep.category}
                    </span>
                  </div>
                  <span className="text-xs font-sans text-zinc-400">
                    {ep.summary}
                  </span>
                </div>

                {/* Body Content */}
                <div className="p-5 space-y-5">
                  <p className="text-xs text-zinc-300 leading-relaxed">
                    {ep.description}
                  </p>

                  {ep.mathConcept && (
                    <div className="p-3 bg-zinc-950/70 border border-purple-900/40 rounded flex items-center justify-between gap-4">
                      <div className="flex items-center gap-2 text-xs font-mono text-purple-400">
                        <Sparkles className="w-3.5 h-3.5 flex-shrink-0" />
                        <span>Core Formulation:</span>
                      </div>
                      <div className="font-mono text-xs overflow-x-auto text-zinc-200">
                        <KaTeX math={ep.mathConcept} />
                      </div>
                    </div>
                  )}

                  {/* Query Parameters Table */}
                  {ep.params.length > 0 && (
                    <div>
                      <h4 className="text-xs font-mono uppercase tracking-wider text-zinc-500 mb-2">Query Parameters</h4>
                      <div className="border border-zinc-800 rounded overflow-hidden">
                        <table className="w-full text-left text-xs font-mono">
                          <thead className="bg-zinc-950/80 text-zinc-400 border-b border-zinc-800">
                            <tr>
                              <th className="px-3 py-2">Parameter</th>
                              <th className="px-3 py-2">Type</th>
                              <th className="px-3 py-2">Required</th>
                              <th className="px-3 py-2">Default</th>
                              <th className="px-3 py-2">Description</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-zinc-800/60 text-zinc-300">
                            {ep.params.map((p, pIdx) => (
                              <tr key={pIdx} className="hover:bg-zinc-800/30">
                                <td className="px-3 py-2 font-semibold text-emerald-400">{p.name}</td>
                                <td className="px-3 py-2 text-zinc-400">{p.type}</td>
                                <td className="px-3 py-2">
                                  {p.required ? (
                                    <span className="text-amber-400 font-semibold">yes</span>
                                  ) : (
                                    <span className="text-zinc-500">no</span>
                                  )}
                                </td>
                                <td className="px-3 py-2 text-zinc-400">{p.defaultVal || "—"}</td>
                                <td className="px-3 py-2 text-zinc-400 font-sans">{p.desc}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Code Snippets Accordion */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {/* cURL & Python */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs font-mono text-zinc-400">
                        <span>Client Request Examples</span>
                        <button
                          onClick={() => copyToClipboard(ep.samplePython, idx * 10)}
                          className="flex items-center gap-1 text-zinc-400 hover:text-zinc-200 transition-colors"
                        >
                          {copiedIndex === idx * 10 ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                          <span>{copiedIndex === idx * 10 ? "Copied" : "Copy Python"}</span>
                        </button>
                      </div>
                      <div className="bg-zinc-950 border border-zinc-800 rounded p-3 text-xs font-mono text-zinc-300 overflow-x-auto max-h-56">
                        <div className="text-zinc-500 mb-2"># cURL</div>
                        <code className="text-emerald-400 block mb-3 select-all">{ep.sampleCurl}</code>
                        <div className="text-zinc-500 mb-2"># Python (httpx / polars)</div>
                        <pre className="text-zinc-200">{ep.samplePython}</pre>
                      </div>
                    </div>

                    {/* JSON Response Preview */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs font-mono text-zinc-400">
                        <span>Sample Response (200 OK)</span>
                        <button
                          onClick={() => copyToClipboard(ep.responsePreview, idx * 10 + 1)}
                          className="flex items-center gap-1 text-zinc-400 hover:text-zinc-200 transition-colors"
                        >
                          {copiedIndex === idx * 10 + 1 ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                          <span>{copiedIndex === idx * 10 + 1 ? "Copied" : "Copy JSON"}</span>
                        </button>
                      </div>
                      <div className="bg-zinc-950 border border-zinc-800 rounded p-3 text-xs font-mono text-zinc-400 overflow-x-auto max-h-56">
                        <pre className="text-emerald-300/90">{ep.responsePreview}</pre>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 2: Polars Guide */}
      {activeTab === "polars" && (
        <div className="space-y-8">
          <div className="p-5 bg-gradient-to-br from-cyan-950/30 to-zinc-900 border border-cyan-900/40 rounded-lg space-y-3">
            <h3 className="text-base font-mono font-bold text-cyan-400 flex items-center gap-2">
              <Cpu className="w-5 h-5" />
              High-Throughput Local Lake Access with Polars
            </h3>
            <p className="text-xs text-zinc-300 leading-relaxed max-w-4xl">
              CryptoLake stores data directly in standard Apache Parquet format using a Hive-partitioned directory tree:
              <br />
              <code className="text-cyan-300 bg-zinc-950 px-2 py-0.5 rounded text-[11px] mt-1 inline-block">
                data/ohlcv/exchange=&#123;exchange&#125;/interval=&#123;interval&#125;/year=&#123;YYYY&#125;/month=&#123;MM&#125;/&#123;symbol&#125;_&#123;YYYY-MM-DD&#125;.parquet
              </code>
              <br />
              Because Parquet is columnar and snappy-compressed, you do not need to query the HTTP REST server for local quant workflows—you can scan the files directly in Python with zero memory overhead using Polars lazy frames.
            </p>
          </div>

          {/* Snippet 1: Out-of-core scanning */}
          <div className="bg-zinc-900/70 border border-zinc-800 rounded-lg p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-mono font-semibold text-zinc-200 flex items-center gap-2">
                <Code2 className="w-4 h-4 text-emerald-400" />
                <span>1. Out-of-Core Multi-Exchange Candle Aggregation</span>
              </div>
              <button
                onClick={() => copyToClipboard(`import polars as pl

# Out-of-core partition scan across all exchanges
q = (
    pl.scan_parquet("data/ohlcv/**/*.parquet")
    .filter(pl.col("symbol") == "BTC/USDT")
    .group_by(["timestamp", "symbol"])
    .agg([
        pl.col("close").mean().alias("twap_close"),
        pl.col("volume").sum().alias("aggregate_volume"),
        pl.col("exchange").n_unique().alias("num_exchanges")
    ])
    .sort("timestamp")
)

df = q.collect()
print(df)`, 991)}
                className="flex items-center gap-1 text-xs font-mono text-zinc-400 hover:text-white"
              >
                {copiedIndex === 991 ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>Copy Script</span>
              </button>
            </div>
            <pre className="bg-zinc-950 border border-zinc-800 rounded p-4 text-xs font-mono text-zinc-300 overflow-x-auto leading-relaxed">
{`import polars as pl

# Out-of-core partition scan across all exchanges with predicate pushdown
q = (
    pl.scan_parquet("data/ohlcv/**/*.parquet")
    .filter(pl.col("symbol") == "BTC/USDT")
    .group_by(["timestamp", "symbol"])
    .agg([
        pl.col("close").mean().alias("twap_close"),
        pl.col("volume").sum().alias("aggregate_volume"),
        pl.col("exchange").n_unique().alias("num_exchanges")
    ])
    .sort("timestamp")
)

# Execute streaming query
df = q.collect()
print(df)`}
            </pre>
          </div>

          {/* Snippet 2: Log Returns & Volatility */}
          <div className="bg-zinc-900/70 border border-zinc-800 rounded-lg p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-mono font-semibold text-zinc-200 flex items-center gap-2">
                <Code2 className="w-4 h-4 text-cyan-400" />
                <span>2. Log Returns, Rolling Volatility, and Kurtosis</span>
              </div>
              <button
                onClick={() => copyToClipboard(`import polars as pl
import numpy as np

df = pl.read_parquet("data/ohlcv/exchange=binance/interval=1h/**/*.parquet")

returns_df = (
    df.filter(pl.col("symbol") == "ETH/USDT")
    .sort("timestamp")
    .with_columns([
        (pl.col("close") / pl.col("close").shift(1)).log().alias("log_return")
    ])
    .with_columns([
        pl.col("log_return").rolling_std(window_size=24).alias("realized_vol_24h")
    ])
)

kurt = returns_df["log_return"].drop_nulls().kurtosis()
print(f"Sample Excess Kurtosis: {kurt:.4f}")`, 992)}
                className="flex items-center gap-1 text-xs font-mono text-zinc-400 hover:text-white"
              >
                {copiedIndex === 992 ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>Copy Script</span>
              </button>
            </div>
            <pre className="bg-zinc-950 border border-zinc-800 rounded p-4 text-xs font-mono text-zinc-300 overflow-x-auto leading-relaxed">
{`import polars as pl
import numpy as np

# Load target asset directly
df = pl.read_parquet("data/ohlcv/exchange=binance/interval=1h/**/*.parquet")

# Vectorized log-returns & rolling standard deviation
returns_df = (
    df.filter(pl.col("symbol") == "ETH/USDT")
    .sort("timestamp")
    .with_columns([
        (pl.col("close") / pl.col("close").shift(1)).log().alias("log_return")
    ])
    .with_columns([
        pl.col("log_return").rolling_std(window_size=24).alias("realized_vol_24h")
    ])
)

kurt = returns_df["log_return"].drop_nulls().kurtosis()
print(f"Sample Excess Kurtosis: {kurt:.4f}")`}
            </pre>
          </div>
        </div>
      )}

      {/* TAB 3: KCL Reading List & Mathematical Syllabus */}
      {activeTab === "kcl" && (
        <div className="space-y-6">
          <div className="p-5 bg-gradient-to-br from-purple-950/30 to-zinc-900 border border-purple-900/40 rounded-lg space-y-2">
            <h3 className="text-base font-mono font-bold text-purple-400 flex items-center gap-2">
              <Sparkles className="w-5 h-5" />
              BSc Mathematics (Year 2) Theory Crosswalk
            </h3>
            <p className="text-xs text-zinc-300 leading-relaxed max-w-4xl">
              This terminal was built as an extracurricular research sandbox applying the core theoretical curriculum of the King&apos;s College London BSc Mathematics degree to high-frequency decentralized financial telemetry.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {KCL_READINGS.map((item, idx) => (
              <div 
                key={idx} 
                className="bg-zinc-900/60 border border-zinc-800 rounded-lg p-5 space-y-4 hover:border-zinc-700 transition-colors"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-purple-500/10 text-purple-400 border border-purple-500/30 font-semibold">
                      {item.module}
                    </span>
                    <span className="text-xs font-mono text-zinc-500">
                      ({item.kclCode})
                    </span>
                  </div>
                  <a
                    href={item.link}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs font-mono text-emerald-400 hover:text-emerald-300 flex items-center gap-1 group"
                  >
                    <span>Read Paper</span>
                    <ExternalLink className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                  </a>
                </div>

                <div>
                  <h4 className="text-base font-mono font-bold text-zinc-100">
                    {item.title}
                  </h4>
                  <div className="text-xs font-sans text-zinc-400 mt-1">
                    {item.authors} ({item.year}) — <span className="italic text-zinc-500">{item.venue}</span>
                  </div>
                </div>

                <p className="text-xs text-zinc-300 leading-relaxed">
                  {item.annotation}
                </p>

                <div className="flex flex-wrap items-center gap-1.5 pt-2">
                  <span className="text-[11px] font-mono text-zinc-500 mr-1">Key Theoretical Constructs:</span>
                  {item.relevantTopics.map((topic, tIdx) => (
                    <span 
                      key={tIdx} 
                      className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-zinc-800/80 text-zinc-300 border border-zinc-700/60"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
