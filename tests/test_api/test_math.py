from __future__ import annotations

from fastapi.testclient import TestClient

from cryptolake.api.app import create_app

client = TestClient(create_app())


def test_tda_takens_success() -> None:
    resp = client.get("/api/v1/math/tda/takens?symbol=BTC-USDT&exchange=binance&tau=2&dim=3")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC-USDT"
    assert data["dim"] == 3
    assert data["tau"] == 2
    assert "points" in data
    assert len(data["points"]) > 0
    p0 = data["points"][0]
    assert "x" in p0 and "y" in p0 and "z" in p0
    assert "entropy_series" in data


def test_tda_takens_invalid_symbol() -> None:
    resp = client.get("/api/v1/math/tda/takens?symbol=INVALID")
    assert resp.status_code == 400


def test_tda_takens_not_found() -> None:
    resp = client.get("/api/v1/math/tda/takens?symbol=UNKNOWN-PAIR&exchange=binance")
    assert resp.status_code == 404


def test_correlation_geometry_success() -> None:
    resp = client.get("/api/v1/math/geometry/correlation?interval=1h")
    assert resp.status_code == 200
    data = resp.json()
    assert "labels" in data
    assert len(data["labels"]) >= 3
    assert "correlation_matrix" in data
    assert "distance_matrix" in data
    assert "coords_2d" in data
    assert "coords_3d" in data
    assert len(data["coords_2d"]) == len(data["labels"])


def test_distribution_stats_success() -> None:
    resp = client.get("/api/v1/math/stats/distribution?symbol=BTC-USDT&exchange=binance")
    assert resp.status_code == 200
    data = resp.json()
    assert "moments" in data
    assert "mean" in data["moments"]
    assert "excess_kurtosis" in data["moments"]
    assert "jarque_bera" in data
    assert "student_t_fit" in data
    assert "histogram" in data
    assert "qq_plot" in data
    assert len(data["histogram"]) > 0


def test_distribution_stats_invalid_symbol() -> None:
    resp = client.get("/api/v1/math/stats/distribution?symbol=INVALID")
    assert resp.status_code == 400


def test_microstructure_spreads_success() -> None:
    resp = client.get("/api/v1/math/microstructure/spreads?symbol=BTC-USDT")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC-USDT"
    assert "venues" in data
    assert data["venue_count"] > 0
