import sys
from datetime import datetime
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FLASKAPI_DIR = PROJECT_ROOT / "flaskapi"
if str(FLASKAPI_DIR) not in sys.path:
    sys.path.insert(0, str(FLASKAPI_DIR))

import bikeinfo_SQL as bikeinfo_sql


def _pass(msg: str):
    print(f"PASS [P0][Bikeinfo SQL] {msg}")


def test_save_snapshot_empty_returns_zero_counts():
    assert bikeinfo_sql.save_snapshot([]) == {
        "stations_written": 0,
        "availability_written": 0,
    }
    _pass("save_snapshot empty input")


def test_save_snapshot_rejects_non_list_input():
    with pytest.raises(ValueError, match="raw_data must be a list"):
        bikeinfo_sql.save_snapshot({"number": 1})
    _pass("save_snapshot non-list validation")


def test_save_snapshot_filters_transforms_and_writes(monkeypatch):
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

    monkeypatch.setattr(bikeinfo_sql, "engine", FakeEngine())

    raw_data = [
        {
            "number": 100,
            "contract_name": "dublin",
            "name": "A",
            "address": "addr-a",
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
            "number": 100,
            "contract_name": "dublin",
            "name": "A-NEW",
            "address": "addr-b",
            "position": {"lat": 53.1, "lng": -6.1},
            "banking": 0,
            "bonus": 1,
            "bike_stands": 25,
            "available_bike_stands": 8,
            "available_bikes": 17,
            "status": "OPEN",
            "last_update": 1700000300000,
        },
        {"number": None, "name": "invalid"},
    ]

    result = bikeinfo_sql.save_snapshot(raw_data)

    assert result == {"stations_written": 1, "availability_written": 2}
    assert len(calls) == 2

    _station_stmt, station_rows = calls[0]
    _availability_stmt, availability_rows = calls[1]

    assert len(station_rows) == 1
    assert station_rows[0]["number"] == 100
    assert station_rows[0]["name"] == "A-NEW"
    assert station_rows[0]["banking"] is False
    assert station_rows[0]["bonus"] is True

    assert len(availability_rows) == 2
    assert availability_rows[0]["available_bikes"] == 13
    assert availability_rows[1]["available_bikes"] == 17
    assert isinstance(availability_rows[0]["last_update"], datetime)
    assert availability_rows[0]["last_update"].tzinfo is None
    _pass("save_snapshot transform/filter/dedup count")


def test_get_station_sql_returns_first_row(monkeypatch):
    monkeypatch.setattr(
        bikeinfo_sql,
        "_fetch_all",
        lambda sql, params: [{"number": params["station_id"], "name": "A"}, {"number": 2}],
    )

    row = bikeinfo_sql.get_station_sql(42)

    assert row == {"number": 42, "name": "A"}
    _pass("get_station_sql returns first row")


def test_get_station_sql_returns_none_when_no_rows(monkeypatch):
    monkeypatch.setattr(bikeinfo_sql, "_fetch_all", lambda sql, params: [])

    row = bikeinfo_sql.get_station_sql(42)

    assert row is None
    _pass("get_station_sql no rows -> None")
