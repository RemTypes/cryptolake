const API_BASE = ""; // Uses Next.js proxy rewrites

export interface OHLCVCandle {
  timestamp: string;
  exchange: string;
  base: string;
  quote: string;
  interval: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume_base: number;
  volume_quote: number;
  trade_count?: number;
  vwap?: number;
}

export interface TickerItem {
  timestamp: string;
  exchange: string;
  base: string;
  quote: string;
  last_price: number;
  bid_price: number;
  ask_price: number;
  high_24h: number;
  low_24h: number;
  volume_24h_base: number;
  volume_24h_quote: number;
  price_change_pct: number;
}

export interface CompareVenue {
  exchange: string;
  last_price: number;
  bid_price: number;
  ask_price: number;
  volume_24h_quote: number;
  timestamp: string;
}

export interface CompareResult {
  symbol: string;
  base: string;
  quote: string;
  venue_count: number;
  spread_summary: {
    min_price: number;
    max_price: number;
    spread_abs: number;
    spread_bps: number;
    best_buy_venue: string;
    best_buy_price: number;
    best_sell_venue: string;
    best_sell_price: number;
    arbitrage_opportunity: boolean;
    gross_arbitrage_bps: number;
  };
  venues: CompareVenue[];
}

export interface TDAResult {
  symbol: string;
  exchange: string;
  interval: string;
  tau: number;
  dim: number;
  optimal_tau_estimated: number;
  point_count: number;
  autocorrelation: number[];
  points: Array<{
    index: number;
    timestamp: string;
    price: number;
    return: number;
    x: number;
    y: number;
    z: number;
  }>;
  entropy_series: Array<{
    timestamp: string;
    entropy: number;
    price: number;
  }>;
  formula: string;
}

export interface CorrelationGeometryResult {
  labels: string[];
  sample_count: number;
  correlation_matrix: number[][];
  distance_matrix: number[][];
  coords_2d: Array<{
    label: string;
    venue: string;
    symbol: string;
    x: number;
    y: number;
  }>;
  coords_3d: Array<{
    label: string;
    venue: string;
    symbol: string;
    x: number;
    y: number;
    z: number;
  }>;
  eigenvalues: number[];
  explained_variance_ratio: number[];
  metric_formula: string;
}

export interface DistributionStatsResult {
  symbol: string;
  exchange: string;
  interval: string;
  sample_size: number;
  moments: {
    mean: number;
    std_dev: number;
    skewness: number;
    excess_kurtosis: number;
    is_leptokurtic: boolean;
  };
  jarque_bera: {
    statistic: number;
    p_value: number | null;
    is_normal_rejected: boolean;
  };
  student_t_fit: {
    degrees_of_freedom: number;
    location: number;
    scale: number;
  };
  histogram: Array<{ center: number; density: number }>;
  fitted_curves: Array<{
    x: number;
    normal_pdf: number;
    student_t_pdf: number;
  }>;
  qq_plot: Array<{ theoretical: number; sample: number }>;
}

export const api = {
  async getOHLCVExchanges(): Promise<{ exchanges: string[] }> {
    const res = await fetch(`${API_BASE}/api/v1/ohlcv/exchanges`);
    if (!res.ok) throw new Error("Failed to fetch exchanges");
    return res.json();
  },

  async getOHLCV(
    exchange: string,
    symbol: string,
    interval = "1h",
    start?: string,
    end?: string
  ): Promise<OHLCVCandle[]> {
    const params = new URLSearchParams({ interval });
    if (start) params.set("start", start);
    if (end) params.set("end", end);
    const res = await fetch(`${API_BASE}/api/v1/ohlcv/${exchange}/${symbol}?${params.toString()}`);
    if (!res.ok) throw new Error(`Failed to fetch OHLCV: ${res.statusText}`);
    return res.json();
  },

  async getTickers(exchange?: string): Promise<TickerItem[]> {
    const params = new URLSearchParams();
    if (exchange) params.set("exchange", exchange);
    const res = await fetch(`${API_BASE}/api/v1/tickers?${params.toString()}`);
    if (!res.ok) throw new Error("Failed to fetch tickers");
    return res.json();
  },

  async getCompare(symbol: string): Promise<CompareResult> {
    const res = await fetch(`${API_BASE}/api/v1/compare/${symbol}`);
    if (!res.ok) throw new Error(`Failed to fetch compare for ${symbol}`);
    return res.json();
  },

  async getTDATakens(
    symbol = "BTC-USDT",
    exchange = "binance",
    tau = 2,
    dim = 3,
    interval = "1h"
  ): Promise<TDAResult> {
    const params = new URLSearchParams({
      symbol,
      exchange,
      tau: tau.toString(),
      dim: dim.toString(),
      interval,
    });
    const res = await fetch(`${API_BASE}/api/v1/math/tda/takens?${params.toString()}`);
    if (!res.ok) throw new Error(`Failed to fetch TDA Takens: ${res.statusText}`);
    return res.json();
  },

  async getCorrelationGeometry(interval = "1h"): Promise<CorrelationGeometryResult> {
    const params = new URLSearchParams({ interval });
    const res = await fetch(`${API_BASE}/api/v1/math/geometry/correlation?${params.toString()}`);
    if (!res.ok) throw new Error(`Failed to fetch correlation geometry: ${res.statusText}`);
    return res.json();
  },

  async getDistributionStats(
    symbol = "BTC-USDT",
    exchange = "binance",
    interval = "1h"
  ): Promise<DistributionStatsResult> {
    const params = new URLSearchParams({ symbol, exchange, interval });
    const res = await fetch(`${API_BASE}/api/v1/math/stats/distribution?${params.toString()}`);
    if (!res.ok) throw new Error(`Failed to fetch distribution stats: ${res.statusText}`);
    return res.json();
  },

  getDownloadUrl(exchange: string, symbol: string, interval = "1h", format = "parquet"): string {
    return `${API_BASE}/api/v1/download/ohlcv/${exchange}/${symbol}?interval=${interval}&format=${format}`;
  }
};

