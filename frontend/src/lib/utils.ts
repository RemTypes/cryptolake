import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(val: number | null | undefined, decimals = 2): string {
  if (val === null || val === undefined || isNaN(val)) return "—";
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(val);
}

export function formatCurrency(val: number | null | undefined, decimals = 2): string {
  if (val === null || val === undefined || isNaN(val)) return "—";
  return "$" + formatNumber(val, decimals);
}

export function formatBps(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) return "—";
  return (val >= 0 ? "+" : "") + formatNumber(val, 2) + " bps";
}

