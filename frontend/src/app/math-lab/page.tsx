"use client";

import React, { useEffect, useState } from "react";
import { PlotlyChart } from "@/components/PlotlyChart";
import { KaTeX } from "@/components/KaTeX";
import {
  api,
  type TDAResult,
  type CorrelationGeometryResult,
  type DistributionStatsResult,
} from "@/lib/api";
import { formatNumber } from "@/lib/utils";
import {
  Atom,
  Binary,
  Layers,
  Sparkles,
  Info,
  RefreshCw,
  Sliders,
  TrendingDown,
  Activity,
  Maximize2,
} from "lucide-react";

export default function MathLabPage() {
  const [activeTab, setActiveTab] = useState<"tda" | "geometry" | "distribution">("tda");

  // TDA state
  const [tdaSymbol, setTdaSymbol] = useState("BTC-USDT");
  const [tdaExchange, setTdaExchange] = useState("binance");
  const [tau, setTau] = useState<number>(2);
  const [tdaData, setTdaData] = useState<TDAResult | null>(null);
  const [tdaLoading, setTdaLoading] = useState(false);

  // Geometry state
  const [geomData, setGeomData] = useState<CorrelationGeometryResult | null>(null);
  const [geomLoading, setGeomLoading] = useState(false);

  // Distribution state
  const [distSymbol, setDistSymbol] = useState("BTC-USDT");
  const [distExchange, setDistExchange] = useState("binance");
  const [distData, setDistData] = useState<DistributionStatsResult | null>(null);
  const [distLoading, setDistLoading] = useState(false);

  // Loaders
  const loadTDA = async () => {
    setTdaLoading(true);
    try {
      const res = await api.getTDATakens(tdaSymbol, tdaExchange, tau, 3, "1h");
      setTdaData(res);
    } catch (err) {
      console.error("TDA fetch error:", err);
    } finally {
      setTdaLoading(false);
    }
  };

  const loadGeometry = async () => {
    setGeomLoading(true);
    try {
      const res = await api.getCorrelationGeometry("1h");
      setGeomData(res);
    } catch (err) {
      console.error("Geometry fetch error:", err);
    } finally {
      setGeomLoading(false);
    }
  };

  const loadDistribution = async () => {
    setDistLoading(true);
    try {
      const res = await api.getDistributionStats(distSymbol, distExchange, "1h");
      setDistData(res);
    } catch (err) {
      console.error("Distribution fetch error:", err);
    } finally {
      setDistLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "tda") loadTDA();
    if (activeTab === "geometry") loadGeometry();
    if (activeTab === "distribution") loadDistribution();
  }, [activeTab, tdaSymbol, tdaExchange, tau, distSymbol, distExchange]);

  return (
    <div className="space-y-8 font-sans">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-terminal-border pb-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-mono mb-1.5">
            <Atom className="w-3.5 h-3.5" />
            <span>KCL BSc Mathematics Research Laboratory</span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-bold text-white font-mono tracking-tight">
            Quantitative Mathematics & Microstructure Lab
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Empirical topological embeddings, Riemannian metric spaces, and heavy-tailed distribution dynamics.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-terminal-card border border-terminal-border font-mono text-xs">
          <button
            onClick={() => setActiveTab("tda")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
              activeTab === "tda"
                ? "bg-cyan-600 text-white font-semibold shadow-md shadow-cyan-600/25"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>1. Topological TDA</span>
          </button>

          <button
            onClick={() => setActiveTab("geometry")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
              activeTab === "geometry"
                ? "bg-cyan-600 text-white font-semibold shadow-md shadow-cyan-600/25"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Binary className="w-3.5 h-3.5" />
            <span>2. Correlation Metric Spaces</span>
          </button>

          <button
            onClick={() => setActiveTab("distribution")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
              activeTab === "distribution"
                ? "bg-cyan-600 text-white font-semibold shadow-md shadow-cyan-600/25"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>3. Fat Tails & Stats</span>
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: TOPOLOGICAL DATA ANALYSIS (TDA)                                    */}
      {/* ========================================================================= */}
      {activeTab === "tda" && (
        <div className="space-y-6">
          {/* Controls Strip */}
          <div className="flex flex-wrap items-center justify-between gap-4 bg-terminal-card border border-terminal-border rounded-xl p-4 font-mono text-xs">
            <div className="flex flex-wrap items-center gap-4">
              <div>
                <label className="text-slate-500 block mb-1">Asset Pair</label>
                <select
                  value={tdaSymbol}
                  onChange={(e) => setTdaSymbol(e.target.value)}
                  className="bg-slate-900 border border-terminal-border rounded-lg px-3 py-1.5 text-slate-200 font-semibold"
                >
                  <option value="BTC-USDT">BTC-USDT</option>
                  <option value="ETH-USDT">ETH-USDT</option>
                  <option value="SOL-USDT">SOL-USDT</option>
                </select>
              </div>

              <div>
                <label className="text-slate-500 block mb-1">Exchange Venue</label>
                <select
                  value={tdaExchange}
                  onChange={(e) => setTdaExchange(e.target.value)}
                  className="bg-slate-900 border border-terminal-border rounded-lg px-3 py-1.5 text-slate-200 uppercase font-semibold"
                >
                  <option value="binance">Binance</option>
                  <option value="coinbase">Coinbase</option>
                  <option value="kraken">Kraken</option>
                  <option value="okx">OKX</option>
                  <option value="bybit">Bybit</option>
                </select>
              </div>

              <div>
                <label className="text-slate-500 block mb-1">
                  Delay Parameter <KaTeX math="\tau" />: <span className="text-cyan-400 font-bold">{tau}h</span>
                </label>
                <input
                  type="range"
                  min="1"
                  max="12"
                  value={tau}
                  onChange={(e) => setTau(parseInt(e.target.value))}
                  className="w-32 accent-cyan-400"
                />
              </div>
            </div>

            <div className="flex items-center gap-3">
              {tdaData && (
                <div className="text-right">
                  <span className="text-[11px] text-slate-500 block">Optimal Delay Estimate</span>
                  <span className="text-xs text-cyan-400 font-bold">
                    <KaTeX math="\tau^* =" /> {tdaData.optimal_tau_estimated} (autocorrelation decay)
                  </span>
                </div>
              )}
              <button
                onClick={loadTDA}
                disabled={tdaLoading}
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${tdaLoading ? "animate-spin text-cyan-400" : ""}`} />
              </button>
            </div>
          </div>

          {/* 3D Phase Space Chart & Entropy Timeline */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 3D Scatter Plot */}
            <div className="bg-terminal-card border border-terminal-border rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                    <span>Takens&apos; Phase Space Trajectory</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-semibold">
                      <KaTeX math="\mathbb{R}^3" /> Embedding
                    </span>
                  </h3>
                  <p className="text-xs text-slate-400 font-mono">
                    <KaTeX math="v_t = (r_{t - 2\tau},\, r_{t - \tau},\, r_t)" /> — Click and drag to rotate in 3D
                  </p>
                </div>
                <span className="text-xs text-slate-500 font-mono">
                  {tdaData?.point_count || 0} Points
                </span>
              </div>

              {tdaData && (
                <PlotlyChart
                  data={[
                    {
                      type: "scatter3d",
                      mode: "lines+markers",
                      x: tdaData.points.map((p) => p.x),
                      y: tdaData.points.map((p) => p.y),
                      z: tdaData.points.map((p) => p.z),
                      text: tdaData.points.map(
                        (p) =>
                          `${p.timestamp}<br>Price: $${p.price.toLocaleString()}<br>Return: ${(
                            p.return * 100
                          ).toFixed(2)}%`
                      ),
                      hoverinfo: "text",
                      marker: {
                        size: 3.5,
                        color: tdaData.points.map((p) => p.return),
                        colorscale: "Viridis",
                        opacity: 0.85,
                      },
                      line: {
                        color: "rgba(56, 189, 248, 0.35)",
                        width: 1.5,
                      },
                    },
                  ]}
                  layout={{
                    scene: {
                      xaxis: { title: { text: "r_{t-2τ}" }, gridcolor: "#1e293b", zerolinecolor: "#334155" },
                      yaxis: { title: { text: "r_{t-τ}" }, gridcolor: "#1e293b", zerolinecolor: "#334155" },
                      zaxis: { title: { text: "r_t" }, gridcolor: "#1e293b", zerolinecolor: "#334155" },
                      camera: { eye: { x: 1.5, y: 1.5, z: 1.2 } },
                    },
                    margin: { t: 0, r: 0, l: 0, b: 0 },
                  }}
                  style={{ height: "420px" }}
                />
              )}
            </div>

            {/* Rolling Topological Dispersion / Entropy */}
            <div className="bg-terminal-card border border-terminal-border rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                    <span>Rolling Topological Entropy vs Price</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-purple-950 text-purple-400 border border-purple-800/60 font-semibold">
                      Regime Transition Indicator
                    </span>
                  </h3>
                  <p className="text-xs text-slate-400 font-mono">
                    Sharp drops in entropy indicate topological clustering and systemic volatility shifts
                  </p>
                </div>
              </div>

              {tdaData && (
                <PlotlyChart
                  data={[
                    {
                      type: "scatter",
                      mode: "lines",
                      name: "Topological Entropy",
                      x: tdaData.entropy_series.map((e) => e.timestamp),
                      y: tdaData.entropy_series.map((e) => e.entropy),
                      line: { color: "#a855f7", width: 2 },
                      yaxis: "y1",
                    },
                    {
                      type: "scatter",
                      mode: "lines",
                      name: "Close Price ($)",
                      x: tdaData.entropy_series.map((e) => e.timestamp),
                      y: tdaData.entropy_series.map((e) => e.price),
                      line: { color: "#38bdf8", width: 1.5, dash: "dot" },
                      yaxis: "y2",
                    },
                  ]}
                  layout={{
                    yaxis: { title: { text: "Entropy H(D)" }, gridcolor: "#1e293b" },
                    yaxis2: {
                      title: { text: "Price (USD)" },
                      overlaying: "y",
                      side: "right",
                      gridcolor: "transparent",
                    },
                    legend: { orientation: "h", y: -0.15 },
                    margin: { t: 20, r: 40, l: 45, b: 40 },
                  }}
                  style={{ height: "420px" }}
                />
              )}
            </div>
          </div>

          {/* Educational Mathematics Box */}
          <div className="bg-slate-900/80 border border-cyan-500/30 rounded-xl p-6 space-y-4 font-mono text-xs">
            <div className="flex items-center gap-2 text-cyan-400 font-bold text-sm">
              <Info className="w-4 h-4" />
              <span>Mathematical Intuition: Takens' Embedding & Topology</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-slate-300 leading-relaxed">
              <div className="space-y-2">
                <p className="font-semibold text-white">1. Takens&apos; Delay Embedding Theorem</p>
                <p>
                  In dynamical systems, we observe only a 1-dimensional projection of a complex
                  multi-variable attractor (the cryptocurrency market). Floris Takens (1981) proved
                  that the underlying high-dimensional manifold <KaTeX math="\mathcal{M}" /> of dimension <KaTeX math="d" /> can
                  be topologically reconstructed by delay coordinates:
                </p>
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-center text-cyan-300 font-semibold my-2">
                  <KaTeX
                    math="\mathbf{v}(t) = \big(x(t),\, x(t - \tau),\, \dots,\, x(t - (m-1)\tau)\big) \in \mathbb{R}^m"
                    block
                  />
                </div>
                <p className="text-slate-400">
                  Provided <KaTeX math="m \ge 2d + 1" />, this map is a smooth embedding (diffeomorphism),
                  preserving topological invariants such as homology groups and Lyapunov exponents.
                </p>
              </div>

              <div className="space-y-2">
                <p className="font-semibold text-white">2. Vietoris-Rips Complexes &amp; Quant Relevance</p>
                <p>
                  On this point cloud <KaTeX math="X \subset \mathbb{R}^m" />, we construct a parameterized
                  Vietoris-Rips simplicial complex <KaTeX math="\mathcal{VR}(X, \epsilon)" /> where a <KaTeX math="k" />-simplex
                  is formed whenever all pairwise distances are <KaTeX math="\le \epsilon" />.
                </p>
                <p>
                  Rolling topological entropy <KaTeX math="H(\epsilon)" /> measures how uniformly scattered points are
                  in phase space. <span className="text-cyan-400 font-bold">During market crashes</span>,
                  asset dynamics collapse onto low-dimensional manifolds, triggering an immediate drop in
                  topological entropy before price cascades unfold.
                </p>
                <div className="p-2.5 rounded bg-cyan-950/40 border border-cyan-800/40 text-cyan-300 text-[11px]">
                  <strong>Quant Interview Pitch:</strong> "Rather than relying on linear moving
                  averages, I applied Takens' embedding to capture non-linear phase space topology and
                  detect regime shifts prior to volatility surges."
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: RIEMANNIAN CORRELATION GEOMETRY                                    */}
      {/* ========================================================================= */}
      {activeTab === "geometry" && (
        <div className="space-y-6">
          {/* Header Strip */}
          <div className="bg-terminal-card border border-terminal-border rounded-xl p-4 font-mono text-xs flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Binary className="w-4 h-4 text-cyan-400" />
              <span className="text-slate-200 font-semibold">
                Multi-Exchange Metric Space Embedding
              </span>
              <span className="text-slate-500">
                ({geomData?.labels.length || 0} Aligned Pairs & Venues)
              </span>
            </div>
            <button
              onClick={loadGeometry}
              disabled={geomLoading}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${geomLoading ? "animate-spin text-cyan-400" : ""}`} />
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Correlation Heatmap */}
            <div className="bg-terminal-card border border-terminal-border rounded-xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <span>Pairwise Correlation Matrix <KaTeX math="\mathbf{C}" /></span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-semibold">
                  [-1, +1]
                </span>
              </h3>

              {geomData && (
                <PlotlyChart
                  data={[
                    {
                      type: "heatmap",
                      z: geomData.correlation_matrix,
                      x: geomData.labels,
                      y: geomData.labels,
                      colorscale: "RdBu",
                      zmin: -1,
                      zmax: 1,
                      reversescale: true,
                    },
                  ]}
                  layout={{
                    margin: { t: 10, r: 10, l: 90, b: 90 },
                    xaxis: { tickangle: -45 },
                  }}
                  style={{ height: "420px" }}
                />
              )}
            </div>

            {/* Classical MDS 2D Manifold Embedding */}
            <div className="bg-terminal-card border border-terminal-border rounded-xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <span>2D Metric Space Projection (Classical MDS)</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-semibold">
                  Distance <KaTeX math="d_{ij} = \sqrt{2(1 - \rho_{ij})}" />
                </span>
              </h3>
              <p className="text-xs text-slate-400 font-mono">
                Points close together exhibit near-identical returns; separated clusters indicate market segmentation
              </p>

              {geomData && (
                <PlotlyChart
                  data={[
                    {
                      type: "scatter",
                      mode: "markers+text",
                      x: geomData.coords_2d.map((c) => c.x),
                      y: geomData.coords_2d.map((c) => c.y),
                      text: geomData.coords_2d.map((c) => c.label),
                      textposition: "top center",
                      textfont: { color: "#f8fafc", family: "monospace", size: 11 },
                      marker: {
                        size: 14,
                        color: geomData.coords_2d.map((c) => {
                          if (c.venue.toLowerCase().includes("binance")) return "#f59e0b";
                          if (c.venue.toLowerCase().includes("coinbase")) return "#3b82f6";
                          if (c.venue.toLowerCase().includes("kraken")) return "#8b5cf6";
                          if (c.venue.toLowerCase().includes("okx")) return "#10b981";
                          return "#ec4899";
                        }),
                        opacity: 0.9,
                        line: { color: "#ffffff", width: 1.5 },
                      },
                    },
                  ]}
                  layout={{
                    xaxis: { title: { text: "MDS Coordinate 1" }, gridcolor: "#1e293b", zerolinecolor: "#334155" },
                    yaxis: { title: { text: "MDS Coordinate 2" }, gridcolor: "#1e293b", zerolinecolor: "#334155" },
                    margin: { t: 20, r: 20, l: 45, b: 40 },
                  }}
                  style={{ height: "420px" }}
                />
              )}
            </div>
          </div>

          {/* Educational Mathematics Box */}
          <div className="bg-slate-900/80 border border-cyan-500/30 rounded-xl p-6 space-y-4 font-mono text-xs">
            <div className="flex items-center gap-2 text-cyan-400 font-bold text-sm">
              <Info className="w-4 h-4" />
              <span>Mathematical Intuition: Correlation Metric Spaces & MDS</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-slate-300 leading-relaxed">
              <div className="space-y-2">
                <p className="font-semibold text-white">1. Constructing a Formal Metric Space</p>
                <p>
                  While correlation <KaTeX math="\rho_{ij} \in [-1, 1]" /> is not a distance metric (it violates
                  the triangle inequality), Mantegna (1999) proved that transforming correlation via:
                </p>
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-center text-cyan-300 font-semibold my-2">
                  <KaTeX math="d_{ij} = \sqrt{2(1 - \rho_{ij})} = \|\hat{X}_i - \hat{X}_j\|_{L^2}" block />
                </div>
                <p className="text-slate-400">
                  defines a true Euclidean distance metric on the space of zero-mean, unit-variance
                  standardized return vectors <KaTeX math="\hat{X}_i = (X_i - \mu_i)/\sigma_i" />.
                </p>
              </div>

              <div className="space-y-2">
                <p className="font-semibold text-white">2. Classical Multidimensional Scaling</p>
                <p>
                  We project the <KaTeX math="N \times N" /> metric distance matrix into low-dimensional Euclidean
                  space by double-centering:
                </p>
                <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-center text-cyan-300 text-[11px] my-1">
                  <KaTeX math="B = -\frac{1}{2} H D^2 H, \quad H = I - \frac{1}{N}\mathbf{1}\mathbf{1}^T" block />
                </div>
                <p className="text-slate-400">
                  The coordinates correspond to the top eigenvectors of the Gram matrix <KaTeX math="B" />. In
                  portfolio management, this groups co-moving assets geometrically for hierarchical risk
                  parity (HRP) and statistical pairs trading.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: STATISTICAL MICROSTRUCTURE & FAT TAILS                             */}
      {/* ========================================================================= */}
      {activeTab === "distribution" && (
        <div className="space-y-6">
          {/* Controls Strip */}
          <div className="flex flex-wrap items-center justify-between gap-4 bg-terminal-card border border-terminal-border rounded-xl p-4 font-mono text-xs">
            <div className="flex flex-wrap items-center gap-4">
              <div>
                <label className="text-slate-500 block mb-1">Asset Pair</label>
                <select
                  value={distSymbol}
                  onChange={(e) => setDistSymbol(e.target.value)}
                  className="bg-slate-900 border border-terminal-border rounded-lg px-3 py-1.5 text-slate-200 font-semibold"
                >
                  <option value="BTC-USDT">BTC-USDT</option>
                  <option value="ETH-USDT">ETH-USDT</option>
                  <option value="SOL-USDT">SOL-USDT</option>
                </select>
              </div>

              <div>
                <label className="text-slate-500 block mb-1">Exchange</label>
                <select
                  value={distExchange}
                  onChange={(e) => setDistExchange(e.target.value)}
                  className="bg-slate-900 border border-terminal-border rounded-lg px-3 py-1.5 text-slate-200 uppercase font-semibold"
                >
                  <option value="binance">Binance</option>
                  <option value="coinbase">Coinbase</option>
                  <option value="kraken">Kraken</option>
                  <option value="okx">OKX</option>
                  <option value="bybit">Bybit</option>
                </select>
              </div>
            </div>

            <button
              onClick={loadDistribution}
              disabled={distLoading}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${distLoading ? "animate-spin text-cyan-400" : ""}`} />
            </button>
          </div>

          {/* Moments KPI Cards */}
          {distData && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 font-mono text-xs">
              <div className="bg-terminal-card border border-terminal-border rounded-xl p-4 space-y-1">
                <span className="text-slate-500">Sample Volatility (<KaTeX math="\sigma" />)</span>
                <div className="text-lg font-bold text-white">
                  {(distData.moments.std_dev * 100).toFixed(3)}%
                </div>
                <span className="text-[10px] text-slate-500">Hourly standard deviation</span>
              </div>

              <div className="bg-terminal-card border border-terminal-border rounded-xl p-4 space-y-1">
                <span className="text-slate-500">Excess Kurtosis (<KaTeX math="\kappa" />)</span>
                <div className="text-lg font-bold text-amber-400">
                  {distData.moments.excess_kurtosis.toFixed(2)}
                </div>
                <span className="text-[10px] text-amber-500/90 font-semibold">
                  {distData.moments.is_leptokurtic ? "Leptokurtic (Heavy Tails)" : "Platykurtic"}
                </span>
              </div>

              <div className="bg-terminal-card border border-terminal-border rounded-xl p-4 space-y-1">
                <span className="text-slate-500">Student-t Degrees (<KaTeX math="\nu" />)</span>
                <div className="text-lg font-bold text-cyan-400">
                  <KaTeX math="\nu =" /> {distData.student_t_fit.degrees_of_freedom}
                </div>
                <span className="text-[10px] text-slate-500">
                  {distData.student_t_fit.degrees_of_freedom < 5 ? "Extreme Fat Tails" : "Moderate Tails"}
                </span>
              </div>

              <div className="bg-terminal-card border border-terminal-border rounded-xl p-4 space-y-1">
                <span className="text-slate-500">Jarque-Bera Test</span>
                <div className="text-lg font-bold text-rose-400">
                  JB = {distData.jarque_bera.statistic}
                </div>
                <span className="text-[10px] text-rose-400 font-semibold">
                  Normality Rejected (p &lt; 0.001)
                </span>
              </div>
            </div>
          )}

          {/* Distribution Histogram & QQ Plot */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Histogram & Fitted Density Curves */}
            <div className="bg-terminal-card border border-terminal-border rounded-xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <span>Empirical Returns vs Gaussian &amp; Student-t Fits</span>
              </h3>
              <p className="text-xs text-slate-400 font-mono">
                Log returns <KaTeX math="r_t" /> display classic central peaking and fat-tail decay characteristic of financial time series
              </p>

              {distData && (
                <PlotlyChart
                  data={[
                    {
                      type: "bar",
                      name: "Empirical Density",
                      x: distData.histogram.map((h) => h.center),
                      y: distData.histogram.map((h) => h.density),
                      marker: { color: "rgba(56, 189, 248, 0.45)" },
                    },
                    {
                      type: "scatter",
                      mode: "lines",
                      name: "Gaussian Fit (Normal)",
                      x: distData.fitted_curves.map((c) => c.x),
                      y: distData.fitted_curves.map((c) => c.normal_pdf),
                      line: { color: "#f43f5e", width: 2, dash: "dash" },
                    },
                    {
                      type: "scatter",
                      mode: "lines",
                      name: `Student-t Fit (ν=${distData.student_t_fit.degrees_of_freedom})`,
                      x: distData.fitted_curves.map((c) => c.x),
                      y: distData.fitted_curves.map((c) => c.student_t_pdf),
                      line: { color: "#10b981", width: 2.5 },
                    },
                  ]}
                  layout={{
                    xaxis: { title: { text: "Log Return r_t" }, gridcolor: "#1e293b" },
                    yaxis: { title: { text: "Probability Density" }, gridcolor: "#1e293b" },
                    legend: { orientation: "h", y: -0.2 },
                    margin: { t: 20, r: 20, l: 45, b: 40 },
                  }}
                  style={{ height: "420px" }}
                />
              )}
            </div>

            {/* Quantile-Quantile (QQ) Plot */}
            <div className="bg-terminal-card border border-terminal-border rounded-xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <span>Quantile-Quantile (Q-Q) Plot vs Normal Distribution</span>
              </h3>
              <p className="text-xs text-slate-400 font-mono">
                Curvature at extremes reveals tail risk that standard Black-Scholes / Gaussian risk models underestimate
              </p>

              {distData && (
                <PlotlyChart
                  data={[
                    {
                      type: "scatter",
                      mode: "markers",
                      name: "Sample Quantiles",
                      x: distData.qq_plot.map((q) => q.theoretical),
                      y: distData.qq_plot.map((q) => q.sample),
                      marker: { color: "#38bdf8", size: 6, opacity: 0.8 },
                    },
                    {
                      type: "scatter",
                      mode: "lines",
                      name: "Theoretical Normal (y = x)",
                      x: [-3.5, 3.5],
                      y: [-3.5, 3.5],
                      line: { color: "#f43f5e", width: 1.5, dash: "dash" },
                    },
                  ]}
                  layout={{
                    xaxis: { title: { text: "Theoretical Normal Quantiles" }, gridcolor: "#1e293b" },
                    yaxis: { title: { text: "Sample Standardized Quantiles" }, gridcolor: "#1e293b" },
                    legend: { orientation: "h", y: -0.2 },
                    margin: { t: 20, r: 20, l: 45, b: 40 },
                  }}
                  style={{ height: "420px" }}
                />
              )}
            </div>
          </div>

          {/* Educational Mathematics Box */}
          <div className="bg-slate-900/80 border border-cyan-500/30 rounded-xl p-6 space-y-4 font-mono text-xs">
            <div className="flex items-center gap-2 text-cyan-400 font-bold text-sm">
              <Info className="w-4 h-4" />
              <span>Mathematical Intuition: Leptokurtosis & Tail Decay</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-slate-300 leading-relaxed">
              <div className="space-y-2">
                <p className="font-semibold text-white">1. The Stylized Facts of Financial Microstructure</p>
                <p>
                  Benoit Mandelbrot (1963) and Eugene Fama established that speculative price changes
                  systematically violate the Gaussian assumption of Bachelier and Black-Scholes. Two
                  universal stylized facts dominate:
                </p>
                <ul className="list-disc pl-4 space-y-1 text-slate-400">
                  <li>
                    <strong>Heavy Tails (Leptokurtosis):</strong> Excess kurtosis <KaTeX math="\kappa = \frac{\mu_4}{\sigma^4} - 3 > 0" />, meaning extreme outliers occur orders of magnitude more frequently than Gaussian predictions.
                  </li>
                  <li>
                    <strong>Vol Clustered Jumps:</strong> Large returns are followed by large returns of unpredictable sign.
                  </li>
                </ul>
              </div>

              <div className="space-y-2">
                <p className="font-semibold text-white">2. Student&apos;s t Fitting &amp; Risk Management</p>
                <p>
                  The probability density function of Student&apos;s t-distribution with <KaTeX math="\nu" /> degrees of freedom:
                </p>
                <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-center text-cyan-300 text-[11px] my-1">
                  <KaTeX math="f(x) = \frac{\Gamma((\nu+1)/2)}{\sqrt{\pi\nu}\,\Gamma(\nu/2)\,\sigma} \left(1 + \frac{1}{\nu}\left(\frac{x-\mu}{\sigma}\right)^2\right)^{-\frac{\nu+1}{2}}" block />
                </div>
                <p className="text-slate-400">
                  As <KaTeX math="x \to \infty" />, <KaTeX math="f(x) \sim x^{-(\nu+1)}" /> exhibits polynomial (power law) decay
                  rather than exponential Gaussian decay <KaTeX math="e^{-x^2}" />. When <KaTeX math="\nu \le 4" />, the fourth
                  moment (kurtosis) diverges to infinity!
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
