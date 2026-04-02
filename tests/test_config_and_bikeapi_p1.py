import importlib.util
import json
import runpy
import types
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_config_local_env(monkeypatch):
    monkeypatch.setenv("DB_ENV", "local")
    monkeypatch.delenv("JCDECAUX_API_KEY", raising=False)

    cfg = runpy.run_path(str(PROJECT_ROOT / "config.py"))

    assert cfg["DB_HOST"] == "127.0.0.1"
    assert cfg["DB_NAME"] == "COMP30830_SW"
    assert cfg["BIKE_STATUS_URL"] is None


def test_config_rds_env(monkeypatch):
    monkeypatch.setenv("DB_ENV", "rds")

    cfg = runpy.run_path(str(PROJECT_ROOT / "config.py"))

    assert "rds.amazonaws.com" in cfg["DB_HOST"]
    assert cfg["DB_NAME"] == "bikeinfo"


def test_config_invalid_env_raises(monkeypatch):
    monkeypatch.setenv("DB_ENV", "invalid")

    with pytest.raises(ValueError, match="DB_ENV must be 'local' or 'rds'"):
        runpy.run_path(str(PROJECT_ROOT / "config.py"))


def test_cell02_init_database_executes_create_database(monkeypatch):
    script = PROJECT_ROOT / "bikeinfo" / "bikeapi_cells" / "cell02_init_database.py"
    executed_sql = []
    create_engine_calls = []

    class FakeConn:
        def execution_options(self, **kwargs):
            return self

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, stmt):
            executed_sql.append(str(stmt))

    class FakeEngine:
        def connect(self):
            return FakeConn()

    def fake_create_engine(conn_str):
        create_engine_calls.append(conn_str)
        return FakeEngine()

    class Loader:
        @staticmethod
        def exec_module(mod):
            mod.DB_USER = "u"
            mod.DB_PASSWORD = "p"
            mod.DB_HOST = "h"
            mod.DB_PORT = 3306
            mod.DB_NAME = "TEST_DB"

    def fake_spec_from_file_location(_name, _path):
        return types.SimpleNamespace(loader=Loader())

    def fake_module_from_spec(_spec):
        return types.SimpleNamespace()

    import sqlalchemy

    monkeypatch.setattr(sqlalchemy, "create_engine", fake_create_engine)
    monkeypatch.setattr(importlib.util, "spec_from_file_location", fake_spec_from_file_location)
    monkeypatch.setattr(importlib.util, "module_from_spec", fake_module_from_spec)

    runpy.run_path(str(script))

    assert create_engine_calls
    assert create_engine_calls[0].endswith("@h:3306/")
    assert any("CREATE DATABASE IF NOT EXISTS `TEST_DB`" in sql for sql in executed_sql)


def test_cell03_import_json_filters_invalid_and_inserts(tmp_path, monkeypatch):
    script = PROJECT_ROOT / "bikeinfo" / "bikeapi_cells" / "cell03_import_json_to_database.py"

    sample = [
        {
            "number": 101,
            "contract_name": "dublin",
            "name": "X",
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
        {"number": None, "name": "drop"},
    ]
    (tmp_path / "station_status_20260101T000000Z.json").write_text(
        json.dumps(sample), encoding="utf-8"
    )

    execute_calls = []

    class FakeResult:
        @staticmethod
        def first():
            return True

    class FakeConn:
        def execute(self, stmt, params=None):
            execute_calls.append((str(stmt), params))
            if "SHOW INDEX FROM availability" in str(stmt):
                return FakeResult()
            return FakeResult()

    class FakeBegin:
        def __enter__(self):
            return FakeConn()

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeEngine:
        def begin(self):
            return FakeBegin()

    def fake_create_engine(_conn_str):
        return FakeEngine()

    class Loader:
        @staticmethod
        def exec_module(mod):
            mod.DB_USER = "u"
            mod.DB_PASSWORD = "p"
            mod.DB_HOST = "h"
            mod.DB_PORT = 3306
            mod.DB_NAME = "db"
            mod.FOLDER_PATH = str(tmp_path)

    def fake_spec_from_file_location(_name, _path):
        return types.SimpleNamespace(loader=Loader())

    def fake_module_from_spec(_spec):
        return types.SimpleNamespace()

    import sqlalchemy

    monkeypatch.setattr(sqlalchemy, "create_engine", fake_create_engine)
    monkeypatch.setattr(importlib.util, "spec_from_file_location", fake_spec_from_file_location)
    monkeypatch.setattr(importlib.util, "module_from_spec", fake_module_from_spec)

    runpy.run_path(str(script))

    insert_calls = [c for c in execute_calls if isinstance(c[1], list)]
    assert len(insert_calls) == 2

    station_rows = insert_calls[0][1]
    availability_rows = insert_calls[1][1]
    assert len(station_rows) == 1
    assert station_rows[0]["number"] == 101
    assert len(availability_rows) == 1
    assert availability_rows[0]["available_bikes"] == 13


def test_cell03_import_json_empty_dir_inserts_nothing(tmp_path, monkeypatch):
    script = PROJECT_ROOT / "bikeinfo" / "bikeapi_cells" / "cell03_import_json_to_database.py"

    execute_calls = []

    class FakeResult:
        @staticmethod
        def first():
            return True

    class FakeConn:
        def execute(self, stmt, params=None):
            execute_calls.append((str(stmt), params))
            if "SHOW INDEX FROM availability" in str(stmt):
                return FakeResult()
            return FakeResult()

    class FakeBegin:
        def __enter__(self):
            return FakeConn()

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeEngine:
        def begin(self):
            return FakeBegin()

    def fake_create_engine(_conn_str):
        return FakeEngine()

    class Loader:
        @staticmethod
        def exec_module(mod):
            mod.DB_USER = "u"
            mod.DB_PASSWORD = "p"
            mod.DB_HOST = "h"
            mod.DB_PORT = 3306
            mod.DB_NAME = "db"
            mod.FOLDER_PATH = str(tmp_path)

    def fake_spec_from_file_location(_name, _path):
        return types.SimpleNamespace(loader=Loader())

    def fake_module_from_spec(_spec):
        return types.SimpleNamespace()

    import sqlalchemy

    monkeypatch.setattr(sqlalchemy, "create_engine", fake_create_engine)
    monkeypatch.setattr(importlib.util, "spec_from_file_location", fake_spec_from_file_location)
    monkeypatch.setattr(importlib.util, "module_from_spec", fake_module_from_spec)

    runpy.run_path(str(script))

    insert_calls = [c for c in execute_calls if isinstance(c[1], list)]
    assert insert_calls == []
