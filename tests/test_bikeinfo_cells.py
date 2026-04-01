
import ast
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace


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


def test_import_once_from_cell04_transforms_and_inserts(monkeypatch):
    script = Path("bikeinfo/bikeapi_cells/cell04_import_api_to_database.py")

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return [
                {
                    "number": 100,
                    "contract_name": "dublin",
                    "name": "A",
                    "address": "addr",
                    "position": {"lat": 53.0, "lng": -6.0},
                    "banking": 1,
                    "bonus": 0,
                    "bike_stands": 20,
                    "available_bike_stands": 7,
                    "available_bikes": 13,
                    "status": "OPEN",
                    "last_update": 1700000000000,
                },
                {
                    "number": None,
                    "name": "skip",
                },
            ]

    class FakeRequests:
        @staticmethod
        def get(url, timeout):
            assert timeout == 20
            return FakeResponse()

    calls = []

    class FakeConn:
        def execute(self, stmt, params):
            calls.append((stmt, params))

    class FakeBegin:
        def __enter__(self):
            return FakeConn()

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeEngine:
        def begin(self):
            return FakeBegin()

    import_once = _load_function_from_script(
        script,
        "import_once",
        {
            "requests": FakeRequests,
            "config": SimpleNamespace(BIKE_STATUS_URL="http://example.test"),
            "datetime": datetime,
            "timezone": timezone,
            "engine": FakeEngine(),
            "station_insert": "station_stmt",
            "availability_insert": "availability_stmt",
        },
    )

    import_once()

    assert len(calls) == 2
    station_stmt, station_params = calls[0]
    availability_stmt, availability_params = calls[1]
    assert station_stmt == "station_stmt"
    assert availability_stmt == "availability_stmt"
    assert len(station_params) == 1
    assert station_params[0]["number"] == 100
    assert len(availability_params) == 1
    assert availability_params[0]["available_bikes"] == 13
    assert availability_params[0]["last_update"] is not None


def test_fetch_and_save_once_from_cell01_writes_json(tmp_path):
    script = Path("bikeinfo/bikeapi_cells/cell01_fetch_status_to_json.py")
    payload = [{"number": 1, "name": "X"}]

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return payload

    class FakeRequests:
        @staticmethod
        def get(url, timeout):
            assert timeout == 20
            return FakeResponse()

    fetch_and_save_once = _load_function_from_script(
        script,
        "fetch_and_save_once",
        {
            "datetime": datetime,
            "timezone": timezone,
            "json": json,
            "requests": FakeRequests,
            "config": SimpleNamespace(BIKE_STATUS_URL="http://example.test"),
            "output_dir": tmp_path,
        },
    )

    fetch_and_save_once()

    files = list(tmp_path.glob("station_status_*.json"))
    assert len(files) == 1
    saved = json.loads(files[0].read_text(encoding="utf-8"))
    assert saved == payload
