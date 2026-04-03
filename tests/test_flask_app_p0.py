import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FLASKAPI_DIR = PROJECT_ROOT / "flaskapi"
if str(FLASKAPI_DIR) not in sys.path:
    sys.path.insert(0, str(FLASKAPI_DIR))

import app as app_module


def _pass(msg: str):
    print(f"PASS [P0][Flask Routes] {msg}")


@pytest.fixture()
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client


def test_forecast_success(client, monkeypatch):
    payload = [{"forecast_time": "10:00", "temperature": 10}]
    monkeypatch.setattr(app_module, "get_forecast", lambda: payload)

    resp = client.get("/forecast")

    assert resp.status_code == 200
    assert resp.get_json() == payload
    _pass("/forecast success")


def test_forecast_api_unavailable(client, monkeypatch):
    monkeypatch.setattr(app_module, "get_forecast", lambda: None)

    resp = client.get("/forecast")

    assert resp.status_code == 500
    assert resp.get_json()["error"] == "Forecast API unavailable"
    _pass("/forecast unavailable branch")


def test_stations_refresh_api_unavailable(client, monkeypatch):
    monkeypatch.setattr(app_module, "fetch_stations_raw", lambda: None)

    resp = client.get("/stations/refresh")

    assert resp.status_code == 500
    assert resp.get_json()["error"] == "Bike API unavailable"
    _pass("/stations/refresh api unavailable branch")


def test_stations_refresh_success(client, monkeypatch):
    monkeypatch.setattr(app_module, "fetch_stations_raw", lambda: [{"number": 1}])
    monkeypatch.setattr(
        app_module,
        "save_snapshot",
        lambda raw: {"stations_written": len(raw), "availability_written": len(raw)},
    )

    resp = client.get("/stations/refresh")

    assert resp.status_code == 200
    assert resp.get_json() == {"stations_written": 1, "availability_written": 1}
    _pass("/stations/refresh success")


def test_stations_refresh_handles_exception(client, monkeypatch):
    monkeypatch.setattr(app_module, "fetch_stations_raw", lambda: [{"number": 1}])

    def raise_error(_raw):
        raise RuntimeError("insert failed")

    monkeypatch.setattr(app_module, "save_snapshot", raise_error)

    resp = client.get("/stations/refresh")

    assert resp.status_code == 500
    assert "/stations/refresh failed" in resp.get_json()["error"]
    _pass("/stations/refresh exception branch")


def test_station_info_success(client, monkeypatch):
    monkeypatch.setattr(app_module, "get_station", lambda station_id: {"number": station_id})
    monkeypatch.setattr(app_module, "get_weather", lambda: {"temperature": 12})

    resp = client.get("/station/42/info")

    assert resp.status_code == 200
    assert resp.get_json() == {
        "station": {"number": 42},
        "weather": {"temperature": 12},
    }
    _pass("/station/<id>/info success")


def test_station_info_data_unavailable(client, monkeypatch):
    monkeypatch.setattr(app_module, "get_station", lambda _station_id: None)
    monkeypatch.setattr(app_module, "get_weather", lambda: {"temperature": 12})

    resp = client.get("/station/42/info")

    assert resp.status_code == 500
    assert resp.get_json()["error"] == "Data unavailable"
    _pass("/station/<id>/info unavailable branch")


def test_stations_sql_handles_exception(client, monkeypatch):
    def raise_error():
        raise RuntimeError("db down")

    monkeypatch.setattr(app_module, "get_stations_sql", raise_error)

    resp = client.get("/stations_SQL")

    assert resp.status_code == 500
    assert "Data not found" in resp.get_json()["error"]
    _pass("/stations_SQL exception branch")


def test_availability_sql_handles_exception(client, monkeypatch):
    def raise_error():
        raise RuntimeError("db down")

    monkeypatch.setattr(app_module, "get_availability_sql", raise_error)

    resp = client.get("/availability_SQL")

    assert resp.status_code == 500
    assert "db down" in resp.get_json()["error"]
    _pass("/availability_SQL exception branch")


def test_station_history_handles_exception(client, monkeypatch):
    def raise_error(_station_id):
        raise RuntimeError("db down")

    monkeypatch.setattr(app_module, "get_station_history_sql", raise_error)

    resp = client.get("/station/42/history")

    assert resp.status_code == 500
    assert "db down" in resp.get_json()["error"]
    _pass("/station/<id>/history exception branch")
