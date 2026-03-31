import sys
from pathlib import Path

import pytest


# app.py uses local imports (from openweather import ...), so add flaskapi to path.
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


def test_weather_success(client, monkeypatch):
    monkeypatch.setattr(app_module, "get_weather", lambda: {"temp": 12, "desc": "cloudy"})

    resp = client.get("/weather")

    assert resp.status_code == 200
    assert resp.get_json() == {"temp": 12, "desc": "cloudy"}


def test_weather_api_unavailable(client, monkeypatch):
    monkeypatch.setattr(app_module, "get_weather", lambda: None)

    resp = client.get("/weather")

    assert resp.status_code == 500
    assert "error" in resp.get_json()


def test_stations_success(client, monkeypatch):
    fake_data = [{"number": 42, "name": "Test Station"}]
    monkeypatch.setattr(app_module, "get_latest_stations_view", lambda: fake_data)

    resp = client.get("/stations")

    assert resp.status_code == 200
    assert resp.get_json() == fake_data


def test_stations_handles_exception(client, monkeypatch):
    def raise_error():
        raise RuntimeError("db down")

    monkeypatch.setattr(app_module, "get_latest_stations_view", raise_error)

    resp = client.get("/stations")

    assert resp.status_code == 500
    assert "error" in resp.get_json()


def test_station_sql_info_not_found(client, monkeypatch):
    monkeypatch.setattr(app_module, "get_station_sql", lambda station_id: None)

    resp = client.get("/stations_SQL/99999/info")

    assert resp.status_code == 404
    assert resp.get_json()["error"] == "Station not found"


if __name__ == "__main__":
    # Allow direct execution: python tests/test_flask_app.py
    raise SystemExit(pytest.main(["-v", "-rA", __file__]))
