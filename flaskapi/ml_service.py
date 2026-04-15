from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd

from bikeinfo_SQL import get_prediction_db_features
from openweather import get_forecast

# 项目根目录，用于定位模型文件。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "machine_learning" / "ridge_regression_model.joblib"
META_PATHS = [
    PROJECT_ROOT / "machine_learning" / "ridge_regression_model_meta.joblib",
    PROJECT_ROOT / "machine_learning" / "linear_regression_lag_model_meta.joblib",
]
APP_LOCAL_TZ = ZoneInfo("Europe/Dublin")

# 模型与元数据在模块加载时初始化一次，避免每次请求重复加载。
MODEL = None
MODEL_FEATURES = []
MODEL_TARGET = "available_bikes"

try:
    MODEL = joblib.load(MODEL_PATH)
    for p in META_PATHS:
        if p.exists():
            m = joblib.load(p)
            MODEL_FEATURES = list(m.get("features", []))
            MODEL_TARGET = str(m.get("target", MODEL_TARGET))
            break
except Exception:
    MODEL = None
    MODEL_FEATURES = []


def _features():
    """
    Return model feature names in prediction order.

    :returns: Ordered feature names used for inference.
    :rtype: list[str]
    """
    if MODEL is not None and hasattr(MODEL, "feature_names_in_"):
        return list(MODEL.feature_names_in_)
    return list(MODEL_FEATURES)


def _build_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Align input rows to the model's expected feature columns.

    :param df: Input feature rows.
    :type df: pandas.DataFrame
    :returns: Feature matrix aligned to model columns.
    :rtype: pandas.DataFrame
    """
    expected = _features()
    if not expected:
        raise ValueError("Model feature metadata is empty.")

    work = df.copy()

    # Support one-hot station columns when client sends raw number.
    if any(c.startswith("number_") for c in expected) and "number" not in expected:
        if "number" not in work.columns:
            raise ValueError("Missing required feature: number")
        station_as_str = pd.to_numeric(work["number"], errors="coerce").astype("Int64").astype(str)
        one_hot_cols = [c for c in expected if c.startswith("number_") and c not in work.columns]
        if one_hot_cols:
            one_hot_data = {
                c: (station_as_str == c[len("number_") :]).astype(int)
                for c in one_hot_cols
            }
            # Build one-hot columns in one shot to avoid DataFrame fragmentation.
            one_hot_df = pd.DataFrame(one_hot_data, index=work.index)
            work = pd.concat([work, one_hot_df], axis=1)

    # Align all expected columns in one shot and fill missing values with 0.
    return work.reindex(columns=expected, fill_value=0)


def _post_process(raw_pred, capacity=None):
    """
    Post-process predictions with thresholding, clipping, and rounding.

    :param raw_pred: Raw model predictions.
    :type raw_pred: array-like
    :param capacity: Optional station capacity upper bound.
    :type capacity: array-like | float | None
    :returns: Integer bike predictions.
    :rtype: numpy.ndarray
    """
    pred = np.where(raw_pred < 3, 0, raw_pred)
    pred = np.clip(pred, 0, capacity if capacity is not None else None)
    return np.rint(pred).astype(int)


def _to_utc_pair(local_naive_dt: datetime):
    """
    Convert a Dublin local naive datetime to UTC aware/naive pair.

    :param local_naive_dt: Local datetime without tzinfo.
    :type local_naive_dt: datetime
    :returns: ``(utc_aware, utc_naive)`` pair.
    :rtype: tuple[datetime, datetime]
    """
    local_aware = local_naive_dt.replace(tzinfo=APP_LOCAL_TZ)
    utc_aware = local_aware.astimezone(timezone.utc)
    return utc_aware, utc_aware.replace(tzinfo=None)


def _pick_forecast(target_utc_aware, forecast_rows):
    """
    Pick the forecast row closest to the target UTC time.

    :param target_utc_aware: Target UTC datetime.
    :type target_utc_aware: datetime
    :param forecast_rows: Forecast rows containing ``dt`` timestamps.
    :type forecast_rows: list[dict] | None
    :returns: Closest forecast row or ``None``.
    :rtype: dict | None
    """
    if not forecast_rows:
        return None
    ts = target_utc_aware.timestamp()
    return min(forecast_rows, key=lambda row: abs(float(row.get("dt", 0)) - ts))


def _weather_to_features(weather):
    """
    Map weather payload to model weather features with safe defaults.

    :param weather: Forecast/weather payload.
    :type weather: dict | None
    :returns: ``(temp, pressure, humidity_bin)``.
    :rtype: tuple[float, float, int]
    """
    if not weather:
        return 20.0, 1000.0, 0
    temp = float(weather.get("temperature") or 20.0)
    pressure = float(weather.get("pressure") or 1000.0)
    humidity_bin = 1 if float(weather.get("humidity") or 0.0) > 90 else 0
    return temp, pressure, humidity_bin


def parse_predict_query_args(args):
    """
    Parse and validate ``station_id`` and ``datetime`` query parameters.

    :param args: Request query mapping.
    :type args: werkzeug.datastructures.MultiDict
    :returns: ``(station_id, target_dt, err)``.
    :rtype: tuple[int | None, datetime | None, tuple[dict, int] | None]
    """
    station_id_raw = args.get("station_id") # URL query params are always strings, e.g. station_id=42
    dt_raw = args.get("datetime") # Expecting format like datetime=2024-06-01%2015:30:00 (URL-encoded space)

    if not station_id_raw or not dt_raw:
        return None, None, (
            {
                "error": "Missing required query params: station_id, datetime",
                "expected_datetime_format": "%Y-%m-%d %H:%M:%S",
            },
            400,
        )

    try:
        station_id = int(station_id_raw)
    except (TypeError, ValueError):
        return None, None, ({"error": "station_id must be an integer"}, 400)

    try:
        target_dt = datetime.strptime(dt_raw, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None, None, (
            {
                "error": "Invalid datetime format",
                "expected_datetime_format": "%Y-%m-%d %H:%M:%S",
            },
            400,
        )

    return station_id, target_dt, None


def predict_from_payload(payload):
    """
    Run prediction directly from request payload features.

    :param payload: Single feature row or list of rows.
    :type payload: dict | list[dict] | None
    :returns: ``(response_body, status_code)``.
    :rtype: tuple[dict, int]
    """
    if MODEL is None:
        return {"error": "Model not loaded. Train/save model first."}, 500
    if payload is None:
        return {"error": "Invalid JSON body"}, 400
    # 支持单条记录（dict）或多条记录（list of dicts）。
    rows = payload if isinstance(payload, list) else [payload]
    df = pd.DataFrame(rows)
    x = _build_matrix(df)
    raw_pred = MODEL.predict(x)

    capacity = df["capacity"].to_numpy() if "capacity" in df.columns else None
    pred = _post_process(raw_pred, capacity)

    return {
        "target": MODEL_TARGET,
        "features": _features(),
        "raw_pred": raw_pred.tolist(),
        "pred_available_bikes": pred.tolist(),
    }, 200


def predict_by_station_and_datetime(station_id, target_dt_local_naive):
    """
    Build features from station/time context and return prediction result.

    :param station_id: Station identifier.
    :type station_id: int
    :param target_dt_local_naive: Local target datetime.
    :type target_dt_local_naive: datetime
    :returns: ``(response_body, status_code)``.
    :rtype: tuple[dict, int]
    """
    if MODEL is None:
        return {"error": "Model not loaded. Train/save model first."}, 500

    # 统一转换到 UTC，避免夏令时带来的 1 小时偏差。
    target_utc_aware, target_utc_naive = _to_utc_pair(target_dt_local_naive)
    db_feat = get_prediction_db_features(station_id, target_utc_naive)
    if not db_feat:
        return {"error": f"Station {station_id} not found"}, 404

    weather = _pick_forecast(target_utc_aware, get_forecast(full_series=True))
    temp, pressure, humidity_bin = _weather_to_features(weather)
    capacity = float(db_feat.get("capacity") or 0)
    station_number = int(db_feat.get("number", station_id))
    bikes_same_slot_mean = float(db_feat.get("bikes_same_slot_mean") or 0)
    bikes_1d_mean = float(db_feat.get("bikes_1d_mean") or bikes_same_slot_mean or 0)

    row = {
        "number": station_number,
        "capacity": capacity,
        "day": int(target_utc_naive.day),
        "hour": int(target_utc_naive.hour),
        "minute": int(target_utc_naive.minute),
        "temp": temp,
        "pressure": pressure,
        "humidity": int(humidity_bin),
        "lng": float(db_feat.get("lng")),
        "lat": float(db_feat.get("lat")),
        "bikes_1d_mean": bikes_1d_mean,
        "bikes_same_slot_mean": bikes_same_slot_mean,
    }

    x = _build_matrix(pd.DataFrame([row]))
    raw_pred = MODEL.predict(x)
    pred = _post_process(raw_pred, capacity if capacity > 0 else None)

    debug_payload = {
        "target_time_local": target_dt_local_naive.strftime("%Y-%m-%d %H:%M:%S"),
        "target_time_utc": target_utc_aware.strftime("%Y-%m-%d %H:%M:%S"),
        # Requested debug keys
        "feature_values": row,
        "forecast_matched_time": weather.get("forecast_time") if weather else None,
        "db_stats": {
            "bikes_1d_mean": db_feat.get("bikes_1d_mean"),
            "bikes_same_slot_mean": db_feat.get("bikes_same_slot_mean"),
        },
        # Backward-compatible keys
        "selected_forecast_time": weather.get("forecast_time") if weather else None,
        "weather_raw": weather,
        "db_features_raw": {
            "number": db_feat.get("number"),
            "capacity": db_feat.get("capacity"),
            "lng": db_feat.get("lng"),
            "lat": db_feat.get("lat"),
            "bikes_1d_mean": db_feat.get("bikes_1d_mean"),
            "bikes_same_slot_mean": db_feat.get("bikes_same_slot_mean"),
        },


    }

    return {
        "station_id": station_id,
        "raw_pred": raw_pred.tolist(),
        "pred_available_bikes": pred.tolist(),
        # "debug": debug_payload,
    }, 200
