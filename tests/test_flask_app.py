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


def test_weather_success(client, monkeypatch):
    monkeypatch.setattr(app_module, "get_weather", lambda: {"temperature": 12, "weather": "Clouds"})

    resp = client.get("/weather")

    assert resp.status_code == 200
    assert resp.get_json() == {"temperature": 12, "weather": "Clouds"}


def test_stations_success(client, monkeypatch):
    fake_data = [{"number": 42, "name": "Test Station"}]
    monkeypatch.setattr(app_module, "get_latest_stations_view", lambda: fake_data)

    resp = client.get("/stations")

    assert resp.status_code == 200
    assert resp.get_json() == fake_data


def test_predict_route_returns_service_result(client, monkeypatch):
    monkeypatch.setattr(app_module, "predict_from_payload", lambda _payload: ({"pred_available_bikes": [7]}, 200))

    resp = client.post("/predict", json={"number": 1})

    assert resp.status_code == 200
    assert resp.get_json() == {"pred_available_bikes": [7]}


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-v", "-rA", __file__]))
