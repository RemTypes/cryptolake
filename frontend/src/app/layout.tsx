import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { LakeStatsHeader } from "@/components/LakeStatsHeader";

export const metadata: Metadata = {
  title: "CryptoLake — Quantitative Data Platform & Math Lab",
  description: "Unified crypto market data platform and quantitative research laboratory.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-terminal-bg text-slate-100 flex flex-col font-sans antialiased selection:bg-cyan-500/20 selection:text-cyan-300">
        <Navbar />
        <LakeStatsHeader />
        <main className="flex-1 max-w-7xl w-full mx-auto p-4 lg:p-8">
          {children}
        </main>
        <footer className="border-t border-terminal-border py-6 px-4 lg:px-8 text-center text-xs font-mono text-slate-500 bg-terminal-card/30">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
            <div>CryptoLake Quantitative Platform — Powered by FastAPI, Polars & Next.js</div>
            <div>King's College London Mathematics Portfolio</div>
          </div>
        </footer>
      </body>
    </html>
  );
}

