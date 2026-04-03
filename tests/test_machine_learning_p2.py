import ast
import runpy
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_function_from_script(script_path: Path, func_name: str, injected_globals: dict):
    source = script_path.read_text(encoding="utf-8")
    module_ast = ast.parse(source, filename=str(script_path))
    for node in module_ast.body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            target = node
            break
    else:
        raise AssertionError(f"Function {func_name} not found in {script_path}")

    func_module = ast.Module(body=[target], type_ignores=[])
    compiled = compile(func_module, filename=str(script_path), mode="exec")
    ns = dict(injected_globals)
    exec(compiled, ns)
    return ns[func_name]


def test_predict_bike_availability_builds_features_and_returns_prediction():
    script = PROJECT_ROOT / "machine_learning" / "2. predict_based_on_weather.py"

    class FakeModel:
        def predict(self, df):
            assert list(df.columns) == [
                "station_id",
                "temperature",
                "humidity",
                "wind_speed",
                "precipitation",
                "hour",
                "day_of_week",
            ]
            assert df.iloc[0]["hour"] == 9
            return [17]

    predict_bike_availability = _load_function_from_script(
        script,
        "predict_bike_availability",
        {
            "datetime": datetime,
            "pd": pd,
            "model": FakeModel(),
            "get_weather_forecast": lambda city, date: {
                "temperature": 20.0,
                "humidity": 60.0,
                "wind_speed": 10.0,
                "precipitation": 0.0,
            },
        },
    )

    assert predict_bike_availability(1, "Dublin", "2024-02-25", "09:00") == 17


def test_prediction_flask_predict_missing_params_returns_400():
    ns = runpy.run_path(str(PROJECT_ROOT / "machine_learning" / "3. prediction_flask.py"))
    app = ns["app"]

    with app.test_client() as client:
        resp = client.get("/predict?date=2024-02-25")

    assert resp.status_code == 400
    assert "Missing date, time, or station_id" in resp.get_json()["error"]


def test_prediction_flask_predict_invalid_time_returns_500():
    ns = runpy.run_path(str(PROJECT_ROOT / "machine_learning" / "3. prediction_flask.py"))
    app = ns["app"]
    predict_func = ns["predict"]

    class FakeModel:
        def predict(self, _arr):
            return [9]

    predict_func.__globals__["model"] = FakeModel()
    predict_func.__globals__["fetch_openweather_forecast"] = lambda _date: {
        "temperature": 20,
        "humidity": 60,
        "wind_speed": 5,
        "precipitation": 0,
    }

    with app.test_client() as client:
        resp = client.get("/predict?date=2024-02-25&time=09:00&station_id=32")

    assert resp.status_code == 500
    assert "does not match format" in resp.get_json()["error"]


def test_prediction_flask_predict_success():
    ns = runpy.run_path(str(PROJECT_ROOT / "machine_learning" / "3. prediction_flask.py"))
    app = ns["app"]
    predict_func = ns["predict"]

    class FakeModel:
        def predict(self, arr):
            assert arr.shape == (1, 7)
            return [11]

    predict_func.__globals__["model"] = FakeModel()
    predict_func.__globals__["fetch_openweather_forecast"] = lambda _date: {
        "temperature": 18,
        "humidity": 70,
        "wind_speed": 4,
        "precipitation": 1,
    }

    with app.test_client() as client:
        resp = client.get("/predict?date=2024-02-25&time=09:00:00&station_id=32")

    assert resp.status_code == 200
    assert resp.get_json() == {"predicted_available_bikes": 11}


def test_prediction_flask_station_id_type_boundary_behaviour():
    ns = runpy.run_path(str(PROJECT_ROOT / "machine_learning" / "3. prediction_flask.py"))
    app = ns["app"]
    predict_func = ns["predict"]

    class FakeModel:
        def predict(self, arr):
            return [int(arr[0][0] == "32")]

    predict_func.__globals__["model"] = FakeModel()
    predict_func.__globals__["fetch_openweather_forecast"] = lambda _date: {
        "temperature": 18,
        "humidity": 70,
        "wind_speed": 4,
        "precipitation": 1,
    }

    with app.test_client() as client:
        ok_resp = client.get("/predict?date=2024-02-25&time=09:00:00&station_id=32")
        bad_resp = client.get("/predict?date=2024-02-25&time=09:00:00&station_id=abc")

    assert ok_resp.status_code == 200
    assert bad_resp.status_code == 200
    assert ok_resp.get_json()["predicted_available_bikes"] == 1
    assert bad_resp.get_json()["predicted_available_bikes"] == 0
