import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FLASKAPI_DIR = PROJECT_ROOT / "flaskapi"
if str(FLASKAPI_DIR) not in sys.path:
    sys.path.insert(0, str(FLASKAPI_DIR))

import app as app_module


@pytest.fixture()
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client


def test_weather_unavailable_returns_500(client, monkeypatch):
    monkeypatch.setattr(app_module, "get_weather", lambda: None)

    resp = client.get("/weather")

    assert resp.status_code == 500
    assert resp.get_json()["error"] == "Weather API unavailable"


def test_forecast_success_returns_payload(client, monkeypatch):
    payload = [{"forecast_time": "10:00", "temperature": 10}]
    monkeypatch.setattr(app_module, "get_forecast", lambda: payload)

    resp = client.get("/forecast")

    assert resp.status_code == 200
    assert resp.get_json() == payload


def test_stations_refresh_unavailable_returns_500(client, monkeypatch):
    monkeypatch.setattr(app_module, "fetch_stations_raw", lambda: None)

    resp = client.get("/stations/refresh")

    assert resp.status_code == 500
    assert resp.get_json()["error"] == "Bike API unavailable"


def test_stations_refresh_success_returns_snapshot_result(client, monkeypatch):
    monkeypatch.setattr(app_module, "fetch_stations_raw", lambda: [{"number": 1}])
    monkeypatch.setattr(
        app_module,
        "save_snapshot",
        lambda raw: {"stations_written": len(raw), "availability_written": len(raw)},
    )

    resp = client.get("/stations/refresh")

    assert resp.status_code == 200
    assert resp.get_json() == {"stations_written": 1, "availability_written": 1}


def test_station_history_exception_returns_500(client, monkeypatch):
    def raise_error(_station_id):
        raise RuntimeError("db down")

    monkeypatch.setattr(app_module, "get_station_history_sql", raise_error)

    resp = client.get("/station/42/history")

    assert resp.status_code == 500
    assert "db down" in resp.get_json()["error"]


def test_predict_by_input_invalid_query_returns_400(client, monkeypatch):
    monkeypatch.setattr(
        app_module,
        "parse_predict_query_args",
        lambda _args: (None, None, ({"error": "bad query"}, 400)),
    )

    resp = client.get("/predict/by-input")

    assert resp.status_code == 400
    assert resp.get_json()["error"] == "bad query"
