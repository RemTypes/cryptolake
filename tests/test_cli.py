from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from cryptolake.cli import app

runner = CliRunner()


def test_cli_info() -> None:
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "CryptoLake Configuration" in result.output


def test_cli_status() -> None:
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "OHLCV" in result.output


def test_cli_inspect_default() -> None:
    result = runner.invoke(app, ["inspect"])
    assert result.exit_code == 0
    assert "Parquet Files Found" in result.output


def test_cli_inspect_file() -> None:
    parquet_file = Path("data/ohlcv/binance/BTC-USDT/1h/2026-09-08.parquet")
    if parquet_file.exists():
        result = runner.invoke(app, ["inspect", str(parquet_file), "--rows", "3"])
        assert result.exit_code == 0
        assert "Preview" in result.output
