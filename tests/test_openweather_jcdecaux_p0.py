import sys
from datetime import datetime
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FLASKAPI_DIR = PROJECT_ROOT / "flaskapi"
if str(FLASKAPI_DIR) not in sys.path:
    sys.path.insert(0, str(FLASKAPI_DIR))

import jcdecaux
import openweather


def _pass(msg: str):
    print(f"PASS [P0][External API Wrappers] {msg}")


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_get_weather_success(monkeypatch):
    payload = {
        "main": {"temp": 12.5, "humidity": 77},
        "weather": [{"main": "Clouds"}],
        "wind": {"speed": 4.2},
    }
    monkeypatch.setattr(openweather.requests, "get", lambda _url: FakeResponse(200, payload))

    result = openweather.get_weather()

    assert result == {
        "temperature": 12.5,
        "weather": "Clouds",
        "wind_speed": 4.2,
        "humidity": 77,
    }
    _pass("openweather.get_weather success mapping")


def test_get_weather_non_200_returns_none(monkeypatch):
    monkeypatch.setattr(openweather.requests, "get", lambda _url: FakeResponse(500, {}))

    assert openweather.get_weather() is None
    _pass("openweather.get_weather non-200 -> None")


def test_get_forecast_success(monkeypatch):
    payload = {
        "list": [
            {"dt": 1700000000, "main": {"temp": 10, "humidity": 70}, "weather": [{"main": "Rain"}]},
            {"dt": 1700003600, "main": {"temp": 11, "humidity": 71}, "weather": [{"main": "Clouds"}]},
            {"dt": 1700007200, "main": {"temp": 12, "humidity": 72}, "weather": [{"main": "Clear"}]},
        ]
    }
    monkeypatch.setattr(openweather.requests, "get", lambda _url: FakeResponse(200, payload))

    result = openweather.get_forecast()

    assert len(result) == 2
    assert result[0]["forecast_time"] == datetime.fromtimestamp(1700000000).strftime("%H:%M")
    assert result[0]["temperature"] == 10
    assert result[1]["forecast_time"] == datetime.fromtimestamp(1700007200).strftime("%H:%M")
    assert result[1]["weather"] == "Clear"
    _pass("openweather.get_forecast success mapping")


def test_get_forecast_non_200_returns_none(monkeypatch):
    monkeypatch.setattr(openweather.requests, "get", lambda _url: FakeResponse(503, {}))

    assert openweather.get_forecast() is None
    _pass("openweather.get_forecast non-200 -> None")


def test_get_forecast_short_list_raises_index_error(monkeypatch):
    payload = {
        "list": [
            {"dt": 1700000000, "main": {"temp": 10, "humidity": 70}, "weather": [{"main": "Rain"}]}
        ]
    }
    monkeypatch.setattr(openweather.requests, "get", lambda _url: FakeResponse(200, payload))

    with pytest.raises(IndexError):
        openweather.get_forecast()
    _pass("openweather.get_forecast short list risk exposed")


def test_get_stations_success(monkeypatch):
    payload = [
        {
            "number": 1,
            "name": "A",
            "available_bikes": 5,
            "available_bike_stands": 9,
            "position": {"lat": 53.0, "lng": -6.0},
        }
    ]
    monkeypatch.setattr(jcdecaux.requests, "get", lambda _url: FakeResponse(200, payload))

    result = jcdecaux.get_stations()

    assert result == [
        {
            "number": 1,
            "name": "A",
            "available_bikes": 5,
            "available_stands": 9,
            "lat": 53.0,
            "lng": -6.0,
        }
    ]
    _pass("jcdecaux.get_stations success mapping")


def test_get_stations_non_200_returns_none(monkeypatch):
    monkeypatch.setattr(jcdecaux.requests, "get", lambda _url: FakeResponse(500, {}))

    assert jcdecaux.get_stations() is None
    _pass("jcdecaux.get_stations non-200 -> None")


def test_get_station_found(monkeypatch):
    payload = [
        {
            "number": 7,
            "name": "S7",
            "available_bikes": 6,
            "available_bike_stands": 4,
            "position": {"lat": 1.0, "lng": 2.0},
        }
    ]
    monkeypatch.setattr(jcdecaux.requests, "get", lambda _url: FakeResponse(200, payload))

    result = jcdecaux.get_station(7)

    assert result == {
        "number": 7,
        "name": "S7",
        "available_bikes": 6,
        "available_stands": 4,
        "lat": 1.0,
        "lng": 2.0,
    }
    _pass("jcdecaux.get_station found")


def test_get_station_not_found_returns_none(monkeypatch):
    payload = [
        {
            "number": 8,
            "name": "S8",
            "available_bikes": 2,
            "available_bike_stands": 5,
            "position": {"lat": 1.0, "lng": 2.0},
        }
    ]
    monkeypatch.setattr(jcdecaux.requests, "get", lambda _url: FakeResponse(200, payload))

    assert jcdecaux.get_station(7) is None
    _pass("jcdecaux.get_station not found -> None")


def test_get_station_non_200_returns_none(monkeypatch):
    monkeypatch.setattr(jcdecaux.requests, "get", lambda _url: FakeResponse(500, {}))

    assert jcdecaux.get_station(7) is None
    _pass("jcdecaux.get_station non-200 -> None")


def test_fetch_stations_raw_success(monkeypatch):
    payload = [{"number": 1}, {"number": 2}]
    monkeypatch.setattr(jcdecaux.requests, "get", lambda _url: FakeResponse(200, payload))

    assert jcdecaux.fetch_stations_raw() == payload
    _pass("jcdecaux.fetch_stations_raw success")


def test_fetch_stations_raw_non_200_returns_none(monkeypatch):
    monkeypatch.setattr(jcdecaux.requests, "get", lambda _url: FakeResponse(404, {}))

    assert jcdecaux.fetch_stations_raw() is None
    _pass("jcdecaux.fetch_stations_raw non-200 -> None")
