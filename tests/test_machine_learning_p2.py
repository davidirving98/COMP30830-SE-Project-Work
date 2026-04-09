import sys
from datetime import datetime
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FLASKAPI_DIR = PROJECT_ROOT / "flaskapi"
if str(FLASKAPI_DIR) not in sys.path:
    sys.path.insert(0, str(FLASKAPI_DIR))

import ml_service as ml


class FakeModel:
    def __init__(self, feature_names):
        self.feature_names_in_ = np.array(feature_names)

    def predict(self, x):
        return np.array([5.6] * len(x))


def test_parse_predict_query_args_missing_returns_400():
    station_id, target_dt, err = ml.parse_predict_query_args({})

    assert station_id is None
    assert target_dt is None
    assert err[1] == 400
    assert "Missing required query params" in err[0]["error"]


def test_predict_from_payload_supports_single_record(monkeypatch):
    monkeypatch.setattr(ml, "MODEL", FakeModel(["capacity", "number_3"]))
    monkeypatch.setattr(ml, "MODEL_FEATURES", [])
    monkeypatch.setattr(ml, "MODEL_TARGET", "available_bikes")

    data, status = ml.predict_from_payload({"number": 3, "capacity": 20})

    assert status == 200
    assert data["target"] == "available_bikes"
    assert data["raw_pred"] == [5.6]
    assert data["pred_available_bikes"] == [6]


def test_predict_by_station_and_datetime_returns_basic_prediction(monkeypatch):
    monkeypatch.setattr(
        ml,
        "MODEL",
        FakeModel(
            [
                "capacity",
                "day",
                "hour",
                "minute",
                "temp",
                "pressure",
                "humidity",
                "lng",
                "lat",
                "bikes_1d_mean",
                "bikes_same_slot_mean",
            ]
        ),
    )

    monkeypatch.setattr(
        ml,
        "get_prediction_db_features",
        lambda station_id, _target_time: {
            "number": station_id,
            "capacity": 20,
            "lng": -6.26,
            "lat": 53.34,
            "bikes_1d_mean": 3.0,
            "bikes_same_slot_mean": 7.0,
        },
    )
    monkeypatch.setattr(
        ml,
        "get_forecast",
        lambda full_series=True: [
            {
                "dt": 1775588400,
                "forecast_time": "2026-04-07 20:00:00",
                "temperature": 15.0,
                "pressure": 1015,
                "humidity": 75,
            }
        ],
    )

    data, status = ml.predict_by_station_and_datetime(3, datetime(2026, 4, 7, 19, 30, 0))

    assert status == 200
    assert data["station_id"] == 3
    assert isinstance(data["raw_pred"], list)
    assert isinstance(data["pred_available_bikes"], list)
    assert "debug" in data
    assert "feature_values" in data["debug"]
