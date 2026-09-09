from __future__ import annotations

import asyncio
import datetime
from pathlib import Path
from typing import Annotated

import structlog
import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from cryptolake.config import Settings
from cryptolake.pipeline import storage
from cryptolake.pipeline.ingest import ingest_ohlcv
from cryptolake.sources.binance import BinanceSource
from cryptolake.sources.coingecko import CoinGeckoSource

app = typer.Typer(
    name="cryptolake",
    help="CryptoLake — Unified crypto market data platform.",
    no_args_is_help=True,
)
console = Console()
logger = structlog.get_logger(__name__)


def _parse_symbols(raw: list[str]) -> list[tuple[str, str]]:
    """Parse 'BTC-USDT' or 'BTC/USDT' into ('BTC', 'USDT') tuples."""
    result: list[tuple[str, str]] = []
    for s in raw:
        for sep in ("-", "/"):
            if sep in s:
                parts = s.split(sep, 1)
                result.append((parts[0].upper(), parts[1].upper()))
                break
        else:
            console.print(
                f"[yellow]Warning: Cannot parse symbol '{s}', expected BASE-QUOTE format[/yellow]"
            )
    return result


@app.command()
def ingest(
    exchange: Annotated[
        list[str] | None, typer.Option("--exchange", help="Exchanges to ingest from")
    ] = None,
    symbol: Annotated[
        list[str] | None, typer.Option("--symbol", help="Symbols (e.g. BTC-USDT)")
    ] = None,
    interval: Annotated[
        list[str] | None, typer.Option("--interval", help="Candle intervals")
    ] = None,
    start: Annotated[
        str | None, typer.Option("--start", help="Start datetime (ISO format)")
    ] = None,
    end: Annotated[str | None, typer.Option("--end", help="End datetime (ISO format)")] = None,
    data_dir: Annotated[Path | None, typer.Option("--data-dir", help="Data directory")] = None,
) -> None:
    """Run OHLCV and ticker ingestion."""
    settings = Settings()

    exchanges_to_run = exchange if exchange else ["binance"]
    symbols_raw = symbol if symbol else ["BTC-USDT", "ETH-USDT"]
    intervals_to_run = interval if interval else ["1h"]

    symbols_parsed = _parse_symbols(symbols_raw)
    if not symbols_parsed:
        console.print("[red]No valid symbols provided.[/red]")
        raise typer.Exit(1)

    start_dt = (
        datetime.datetime.fromisoformat(start)
        if start
        else datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
    )
    end_dt = (
        datetime.datetime.fromisoformat(end)
        if end
        else datetime.datetime.now(datetime.timezone.utc)
    )

    target_data_dir = data_dir if data_dir else settings.data_dir
    target_data_dir.mkdir(parents=True, exist_ok=True)

    # Build source instances
    source_map = {
        "binance": BinanceSource,
        "coingecko": CoinGeckoSource,
    }
    sources = []
    for exch in exchanges_to_run:
        cls = source_map.get(exch.lower())
        if cls is None:
            console.print(f"[yellow]Warning: Unknown exchange '{exch}'[/yellow]")
        else:
            sources.append(cls())

    if not sources:
        console.print("[red]No valid sources configured.[/red]")
        raise typer.Exit(1)

    console.print(
        f"[bold green]Ingesting from {len(sources)} source(s): "
        f"{', '.join(s.name for s in sources)}[/bold green]"
    )
    console.print(f"  Symbols: {[f'{b}/{q}' for b, q in symbols_parsed]}")
    console.print(f"  Intervals: {intervals_to_run}")
    console.print(f"  Range: {start_dt.date()} → {end_dt.date()}")

    # Run the async pipeline
    async def _run() -> None:
        for source in sources:
            async with source:
                reports = await ingest_ohlcv(
                    sources=[source],
                    symbols=symbols_parsed,
                    intervals=intervals_to_run,
                    start=start_dt,
                    end=end_dt,
                    data_dir=target_data_dir,
                )

                for report in reports:
                    _print_report(report)

    asyncio.run(_run())
    console.print("[bold green]✓ Ingestion complete![/bold green]")


def _print_report(report: object) -> None:
    """Print an IngestReport as a Rich table."""
    table = Table(title=f"Ingest Report: {getattr(report, 'source', '?')}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Dataset", str(getattr(report, "dataset", "")))
    table.add_row("Rows Written", f"{getattr(report, 'rows_written', 0):,}")
    table.add_row("Files Created", str(getattr(report, "files_created", 0)))
    table.add_row("Duration", f"{getattr(report, 'duration_seconds', 0):.1f}s")

    errors = getattr(report, "errors", [])
    if errors:
        table.add_row("Errors", "\n".join(errors))

    console.print(table)


@app.command()
def serve(
    host: Annotated[str, typer.Option("--host", help="Host to bind to")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", help="Port to bind to")] = 8000,
    reload: Annotated[bool, typer.Option("--reload", help="Enable auto-reload")] = False,
) -> None:
    """Start the API server."""
    console.print(f"[bold green]Starting CryptoLake API on {host}:{port}...[/bold green]")
    uvicorn.run(
        "cryptolake.api.app:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )


@app.command()
def status() -> None:
    """Show available datasets and data freshness."""
    settings = Settings()
    data_dir = settings.data_dir

    if not data_dir.exists():
        console.print("[red]Data directory does not exist. Run 'cryptolake ingest' first.[/red]")
        raise typer.Exit(1)

    datasets = storage.list_available_datasets(data_dir)

    if not any(datasets.values()):
        console.print("[yellow]No data found. Run 'cryptolake ingest' to get started.[/yellow]")
        return

    for ds_name, entries in datasets.items():
        if not entries:
            continue
        table = Table(title=f"📊 {ds_name.upper()}")
        table.add_column("Exchange", style="cyan")
        table.add_column("Symbol", style="green")
        table.add_column("Files", style="magenta")

        for entry in entries:
            table.add_row(
                entry.get("exchange", ""),
                entry.get("symbol", ""),
                entry.get("file_count", ""),
            )

        console.print(table)


@app.command()
def info() -> None:
    """Show current configuration."""
    settings = Settings()

    table = Table(title="CryptoLake Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="magenta")

    for key, value in settings.model_dump().items():
        table.add_row(key, str(value))

    console.print(table)


if __name__ == "__main__":
    app()
