"""Tests for the normalisation utilities."""

from __future__ import annotations

from cryptolake.pipeline.normalise import (
    KNOWN_QUOTE_CURRENCIES,
    KRAKEN_SYMBOL_MAP,
    normalise_symbol_pair,
)


class TestNormaliseSymbolPair:
    """Test exchange-native symbol parsing."""

    def test_binance_btcusdt(self) -> None:
        assert normalise_symbol_pair("BTCUSDT", "binance") == ("BTC", "USDT")

    def test_binance_ethusdt(self) -> None:
        assert normalise_symbol_pair("ETHUSDT", "binance") == ("ETH", "USDT")

    def test_binance_solusdc(self) -> None:
        assert normalise_symbol_pair("SOLUSDC", "binance") == ("SOL", "USDC")

    def test_coinbase_btc_usd(self) -> None:
        assert normalise_symbol_pair("BTC-USD", "coinbase") == ("BTC", "USD")

    def test_coinbase_eth_usd(self) -> None:
        assert normalise_symbol_pair("ETH-USD", "coinbase") == ("ETH", "USD")

    def test_okx_btc_usdt(self) -> None:
        assert normalise_symbol_pair("BTC-USDT", "okx") == ("BTC", "USDT")

    def test_kraken_xxbtzusd(self) -> None:
        base, quote = normalise_symbol_pair("XXBTZUSD", "kraken")
        assert base == "BTC"
        assert quote == "USD"

    def test_bybit_btcusdt(self) -> None:
        assert normalise_symbol_pair("BTCUSDT", "bybit") == ("BTC", "USDT")

    def test_known_quote_currencies_exist(self) -> None:
        assert "USDT" in KNOWN_QUOTE_CURRENCIES
        assert "USD" in KNOWN_QUOTE_CURRENCIES
        assert "BTC" in KNOWN_QUOTE_CURRENCIES

    def test_kraken_symbol_map_has_btc(self) -> None:
        assert KRAKEN_SYMBOL_MAP["XXBT"] == "BTC"
