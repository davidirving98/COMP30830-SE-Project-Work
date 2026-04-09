import sys
from pathlib import Path
from unittest.mock import patch

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FLASKAPI_DIR = PROJECT_ROOT / "flaskapi"
if str(FLASKAPI_DIR) not in sys.path:
    sys.path.insert(0, str(FLASKAPI_DIR))

import app as app_module


@pytest.fixture() # decorator to mark this function as a pytest fixture
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client # test_client is available to the test functions that use this fixture


def test_weather_unavailable_returns_500(client): # test on weather API connection failure in openweather.py
    with patch.object(app_module, "get_weather", return_value=None):
        resp = client.get("/weather")

    assert resp.status_code == 500
    assert resp.get_json()["error"] == "Weather API unavailable"


def test_weather_success_returns_payload(client): # test current weather endpoint in openweather.py
    with patch.object(app_module, "get_weather", return_value={"temperature": 12, "weather": "Clouds"}):
        resp = client.get("/weather")

    assert resp.status_code == 200
    assert resp.get_json() == {"temperature": 12, "weather": "Clouds"}


def test_forecast_success_returns_payload(client): # test on forecast API success in openweather.py
    payload = [{"forecast_time": "10:00", "temperature": 10}]
    with patch.object(app_module, "get_forecast", return_value=payload):
        resp = client.get("/forecast")

    assert resp.status_code == 200
    assert resp.get_json() == payload


def test_stations_refresh_unavailable_returns_500(client): # test on bike API connection failure in jcdecaux.py
    with patch.object(app_module, "fetch_stations_raw", return_value=None):
        resp = client.get("/stations/refresh")

    assert resp.status_code == 500
    assert resp.get_json()["error"] == "Bike API unavailable"


def test_stations_refresh_success_returns_snapshot_result(client): # test on bike API success in jcdecaux.py
    with patch.object(app_module, "fetch_stations_raw", return_value=[{"number": 1}]):
        with patch.object(
            app_module,
            "save_snapshot",
            return_value={"stations_written": 1, "availability_written": 1},
        ):
            resp = client.get("/stations/refresh")

    assert resp.status_code == 200
    assert resp.get_json() == {"stations_written": 1, "availability_written": 1}


def test_stations_success_returns_payload(client): # test stations endpoint in bikeinfo_SQL.py
    fake_data = [{"number": 42, "name": "Test Station"}]
    with patch.object(app_module, "get_latest_stations_view", return_value=fake_data):
        resp = client.get("/stations")

    assert resp.status_code == 200
    assert resp.get_json() == fake_data


def test_station_history_exception_returns_500(client): # test on database connection failure when fetching station history  in bikeinfo_SQL.py
    with patch.object(app_module, "get_station_history_sql", side_effect=RuntimeError("db down")):
        resp = client.get("/station/42/history")

    assert resp.status_code == 500
    assert "db down" in resp.get_json()["error"]


def test_predict_route_returns_service_result(client): # test /predict endpoint function in ml_service.py
    with patch.object(
        app_module,
        "predict_from_payload",
        return_value=({"pred_available_bikes": [7]}, 200),
    ):
        resp = client.post("/predict", json={"number": 1})

    assert resp.status_code == 200
    assert resp.get_json() == {"pred_available_bikes": [7]}


def test_predict_by_input_invalid_query_returns_400(client): # test on invalid prediction query in ml_service.py, by patching the parse_predict_query_args function to return an error response
    with patch.object(
        app_module,
        "parse_predict_query_args",
        return_value=(None, None, ({"error": "bad query"}, 400)),
    ):
        resp = client.get("/predict/by-input")

    assert resp.status_code == 400
    assert resp.get_json()["error"] == "bad query"
