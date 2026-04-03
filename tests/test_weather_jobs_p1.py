import ast
import datetime
from pathlib import Path

import pytest


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


def test_weather_current_to_db_raises_on_non_200():
    script = Path("weatherinfo/scheduler_current_job.py")
    weather_current_to_db = _load_function_from_script(
        script,
        "weather_current_to_db",
        {"datetime": datetime, "text": lambda s: s},
    )

    with pytest.raises(ValueError, match="OpenWeather error"):
        weather_current_to_db({"cod": 500, "message": "bad"}, in_engine=None)


def test_weather_current_to_db_extracts_and_inserts():
    script = Path("weatherinfo/scheduler_current_job.py")
    calls = []

    class FakeConn:
        def execute(self, stmt, vals):
            calls.append((stmt, vals))

    class FakeBegin:
        def __enter__(self):
            return FakeConn()

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeEngine:
        def begin(self):
            return FakeBegin()

    weather_current_to_db = _load_function_from_script(
        script,
        "weather_current_to_db",
        {"datetime": datetime, "text": lambda s: s},
    )

    weather_current_to_db(
        {
            "cod": 200,
            "dt": 1700000000,
            "weather": [{"main": "Clouds", "description": "few clouds"}],
            "main": {"temp": 12.3},
            "wind": {"speed": 4.5},
        },
        FakeEngine(),
    )

    assert len(calls) == 1
    _stmt, vals = calls[0]
    assert vals["main"] == "Clouds"
    assert vals["description"] == "few clouds"
    assert vals["temp"] == 12.3
    assert vals["wind_speed"] == 4.5
    assert isinstance(vals["dt"], datetime.datetime)
    assert isinstance(vals["snapshot_time"], datetime.datetime)


def test_weather_forecast_to_db_limits_to_8_and_inserts():
    script = Path("weatherinfo/scheduler_forecast_job.py")
    calls = []

    class FakeConn:
        def execute(self, stmt, vals):
            calls.append((stmt, vals))

    class FakeBegin:
        def __enter__(self):
            return FakeConn()

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeEngine:
        def begin(self):
            return FakeBegin()

    weather_forecast_to_db = _load_function_from_script(
        script,
        "weather_forecast_to_db",
        {"datetime": datetime, "text": lambda s: s},
    )

    forecast_data = {
        "list": [
            {
                "dt": 1700000000 + (i * 3600),
                "weather": [{"main": f"M{i}", "description": f"D{i}"}],
                "main": {"temp": float(i)},
                "wind": {"speed": float(i) + 0.1},
            }
            for i in range(10)
        ]
    }

    weather_forecast_to_db(forecast_data, FakeEngine())

    assert len(calls) == 8
    first_vals = calls[0][1]
    last_vals = calls[-1][1]
    assert first_vals["main"] == "M0"
    assert last_vals["main"] == "M7"
    assert isinstance(first_vals["future_dt"], datetime.datetime)


def test_weather_forecast_to_db_handles_missing_fields():
    script = Path("weatherinfo/scheduler_forecast_job.py")
    calls = []

    class FakeConn:
        def execute(self, stmt, vals):
            calls.append(vals)

    class FakeBegin:
        def __enter__(self):
            return FakeConn()

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeEngine:
        def begin(self):
            return FakeBegin()

    weather_forecast_to_db = _load_function_from_script(
        script,
        "weather_forecast_to_db",
        {"datetime": datetime, "text": lambda s: s},
    )

    weather_forecast_to_db({"list": [{"dt": 1700000000}]}, FakeEngine())

    assert len(calls) == 1
    assert calls[0]["main"] is None
    assert calls[0]["description"] is None
    assert calls[0]["temp"] is None
    assert calls[0]["wind_speed"] is None
