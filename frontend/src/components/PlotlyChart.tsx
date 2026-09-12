"use client";

import React, { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import type { Layout, Data, Config } from "plotly.js";

// Dynamically import react-plotly.js without SSR
const Plot = dynamic(() => import("react-plotly.js"), {
  ssr: false,
  loading: () => (
    <div className="h-full w-full min-h-[300px] flex items-center justify-center bg-terminal-card border border-terminal-border rounded-lg text-slate-500 font-mono text-sm">
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
        <span>Initializing WebGL Canvas...</span>
      </div>
    </div>
  ),
});

interface PlotlyChartProps {
  data: Data[];
  layout?: Partial<Layout>;
  config?: Partial<Config>;
  className?: string;
  style?: React.CSSProperties;
}

export const PlotlyChart: React.FC<PlotlyChartProps> = ({
  data,
  layout = {},
  config = {},
  className = "",
  style = { width: "100%", height: "100%" },
}) => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="h-full w-full min-h-[300px] flex items-center justify-center bg-terminal-card border border-terminal-border rounded-lg text-slate-500 font-mono text-sm">
        <span>Loading Plotly Engine...</span>
      </div>
    );
  }

  const defaultLayout: Partial<Layout> = {
    autosize: true,
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: {
      color: "#94a3b8",
      family: "ui-monospace, monospace",
      size: 11,
    },
    margin: { t: 30, r: 20, l: 45, b: 40 },
    ...layout,
  };

  const defaultConfig: Partial<Config> = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ["lasso2d", "select2d"],
    ...config,
  };

  return (
    <div className={`relative ${className}`} style={{ minHeight: "350px", ...style }}>
      <Plot
        data={data}
        layout={defaultLayout}
        config={defaultConfig}
        useResizeHandler
        style={{ width: "100%", height: "100%" }}
      />
    </div>
  );
};

