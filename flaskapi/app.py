from flask import Flask, jsonify, render_template, request

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import joblib
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
import config
from openweather import get_weather, get_forecast

from jcdecaux import get_station, fetch_stations_raw
from bikeinfo_SQL import (
    get_stations_sql,
    get_availability_sql,
    get_station_sql,
    get_station_history_sql,
    get_prediction_db_features,
    save_snapshot,
    get_latest_stations_view,
)

app = Flask(__name__)

# ---- ML model (loaded once at startup) ----
# Use Ridge model by default (more stable than plain LinearRegression here).
MODEL_PATH = PROJECT_ROOT / "machine_learning" / "ridge_regression_model.joblib"
META_PATH_CANDIDATES = [
    PROJECT_ROOT / "machine_learning" / "ridge_regression_model_meta.joblib",
    PROJECT_ROOT / "machine_learning" / "linear_regression_lag_model_meta.joblib",
]

MODEL = None
MODEL_FEATURES = []
MODEL_TARGET = "available_bikes"

try:
    MODEL = joblib.load(MODEL_PATH)
    for mp in META_PATH_CANDIDATES:
        if mp.exists():
            meta = joblib.load(mp)
            MODEL_FEATURES = list(meta.get("features", []))
            MODEL_TARGET = str(meta.get("target", MODEL_TARGET))
            break
except Exception:
    # Keep app bootable even when model artifacts are missing.
    MODEL = None
    MODEL_FEATURES = []


def _effective_model_features():
    """Prefer estimator-native feature names when available."""
    if MODEL is not None and hasattr(MODEL, "feature_names_in_"):
        return list(MODEL.feature_names_in_)
    return list(MODEL_FEATURES)


def _build_prediction_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Align request rows to the exact feature order expected by the fitted model.
    Supports one-hot station columns (number_*) when raw 'number' is provided.
    """
    expected = _effective_model_features()
    if not expected:
        raise ValueError("Model feature metadata is empty.")

    work = df.copy()
    has_station_onehot = any(c.startswith("number_") for c in expected)
    raw_number_used = "number" in expected

    # Convert raw station number -> one-hot columns expected by model.
    if has_station_onehot and not raw_number_used:
        if "number" not in work.columns:
            raise ValueError("Missing required feature: number")
        station_as_str = (
            pd.to_numeric(work["number"], errors="coerce").astype("Int64").astype(str)
        )
        for col in [c for c in expected if c.startswith("number_")]:
            station_token = col[len("number_") :]
            work[col] = (station_as_str == station_token).astype(int)

    for c in expected:
        if c not in work.columns:
            work[c] = 0

    return work[expected]


def _pick_forecast_for_target(target_dt, forecast_rows):
    """
    Choose weather features for a target datetime.
    - within 96h: nearest forecast point
    - beyond 96h: latest forecast point with same hour (fallback: latest point)
    """
    if not forecast_rows:
        return None

    now = datetime.now()
    if target_dt > now + timedelta(hours=96):
        same_hour_rows = [
            row for row in forecast_rows
            if datetime.fromtimestamp(int(row.get("dt", 0))).hour == target_dt.hour
        ]
        return same_hour_rows[-1] if same_hour_rows else forecast_rows[-1]

    target_ts = target_dt.timestamp()
    return min(
        forecast_rows,
        key=lambda row: abs(float(row.get("dt", 0)) - target_ts),
    )


def _predict_post_process(raw_pred, capacity=None):
    """Apply common prediction post-processing rules."""
    pred = np.where(raw_pred < 3, 0, raw_pred)
    pred = np.clip(pred, 0, capacity if capacity is not None else None)
    return np.rint(pred).astype(int)


def _parse_predict_query_args(args):
    """Parse and validate /predict/by-input query args."""
    station_id_raw = args.get("station_id")
    dt_raw = args.get("datetime")
    if not station_id_raw or not dt_raw:
        return None, None, (
            jsonify(
                {
                    "error": "Missing required query params: station_id, datetime",
                    "expected_datetime_format": "%Y-%m-%d %H:%M:%S",
                }
            ),
            400,
        )

    try:
        station_id = int(station_id_raw)
    except (TypeError, ValueError):
        return None, None, (jsonify({"error": "station_id must be an integer"}), 400)

    try:
        target_dt = datetime.strptime(dt_raw, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None, None, (
            jsonify(
                {
                    "error": "Invalid datetime format",
                    "expected_datetime_format": "%Y-%m-%d %H:%M:%S",
                }
            ),
            400,
        )
    return station_id, target_dt, None


def _weather_to_features(weather):
    """Map weather payload to model features; fallback to zeros when unavailable."""
    if not weather:
        return 0.0, 0.0, 0, True
    temp = float(weather.get("temperature") or 0.0)
    pressure = float(weather.get("pressure") or 0.0)
    humidity_bin = 1 if float(weather.get("humidity") or 0.0) > 90 else 0
    return temp, pressure, humidity_bin, False


@app.route("/")
def index():
    return render_template("index.html", apikey=config.GOOGLE_MAPS_API_KEY)


@app.route("/stations")
def stations():
    try:
        # Read latest snapshot from DB only.
        # API polling is handled by the background importer (cell04).
        data = get_latest_stations_view()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"/stations failed: {str(e)}"}), 500


@app.route("/stations/refresh")
def stations_refresh():
    try:
        # Manual fallback endpoint: fetch from API and persist now.
        raw_data = fetch_stations_raw()
        if raw_data is None:
            return jsonify({"error": "Bike API unavailable"}), 500
        result = save_snapshot(raw_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"/stations/refresh failed: {str(e)}"}), 500


@app.route("/weather")
def weather():
    data = get_weather()

    if data is None:
        return jsonify({"error": "Weather API unavailable"}), 500

    return jsonify(data)

@app.route("/forecast")
def forecast():
    data = get_forecast()

    if data is None:
        return jsonify({"error": "Forecast API unavailable"}), 500

    return jsonify(data)


@app.route("/station/<int:station_id>/info")
def station_info(station_id):

    station = get_station(station_id)
    weather = get_weather()

    if station is None or weather is None:
        return jsonify({"error": "Data unavailable"}), 500

    return jsonify({"station": station, "weather": weather})


# The following endpoints are for testing the SQL database connection and queries.
@app.route("/stations_SQL")
def stations_sql():
    try:
        return jsonify(get_stations_sql())
    except Exception as e:
        return jsonify({"error": f"Data not found: {str(e)}"}), 500


# This endpoint returns the current availability of bikes and stands for all stations.
@app.route("/availability_SQL")
def availability_sql():
    try:
        return jsonify(get_availability_sql())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# This endpoint returns detailed information about a specific station
@app.route("/stations_SQL/<int:station_id>/info")
def station_sql_info(station_id):
    try:
        station = get_station_sql(station_id)
        if station is None:
            return jsonify({"error": "Station not found"}), 404
        return jsonify(station)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# This endpoint returns the historical availability data for a specific station.
@app.route("/station/<int:station_id>/history")
def station_history(station_id):
    try:
        return jsonify(get_station_history_sql(station_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# This function calls machine learning model to predict the available bikes for a specific station and datetime.
@app.route("/predict", methods=["POST"])
def predict():

    try:
        if MODEL is None:
            return jsonify({"error": "Model not loaded. Train/save model first."}), 500

        payload = request.get_json(force=True, silent=True)
        if payload is None:
            return jsonify({"error": "Invalid JSON body"}), 400

        rows = payload if isinstance(payload, list) else [payload]
        df = pd.DataFrame(rows)

        X = _build_prediction_matrix(df)
        raw_pred = MODEL.predict(X)

        capacity = df["capacity"].to_numpy() if "capacity" in df.columns else None
        pred = _predict_post_process(raw_pred, capacity)

        return jsonify(
            {
                "target": MODEL_TARGET,
                "features": _effective_model_features(),
                "raw_pred": raw_pred.tolist(),
                "pred_available_bikes": pred.tolist(),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/predict/by-input", methods=["GET"])
def predict_by_input():
    try:
        if MODEL is None:
            return jsonify({"error": "Model not loaded. Train/save model first."}), 500

        station_id, target_dt, err = _parse_predict_query_args(request.args)
        if err:
            return err

        db_feat = get_prediction_db_features(station_id, target_dt)
        if not db_feat:
            return jsonify({"error": f"Station {station_id} not found"}), 404

        forecast_rows = get_forecast(full_series=True)
        weather = _pick_forecast_for_target(target_dt, forecast_rows)
        capacity = float(db_feat.get("capacity") or 0)

        # Weather fallback: if forecast is unavailable, continue with DB-only features.
        temp, pressure, humidity_bin, weather_fallback = _weather_to_features(weather)

        row = {
            "number": int(db_feat.get("number", station_id)),
            "capacity": capacity,
            "day": int(target_dt.day),
            "hour": int(target_dt.hour),
            "minute": int(target_dt.minute),
            "temp": temp,
            "pressure": pressure,
            "humidity": int(humidity_bin),
            "lng": float(db_feat.get("lng")),
            "lat": float(db_feat.get("lat")),
            "bikes_1d_mean": float(db_feat.get("bikes_1d_mean") or 0),
            "bikes_same_slot_mean": float(db_feat.get("bikes_same_slot_mean") or 0),
        }

        X = _build_prediction_matrix(pd.DataFrame([row]))
        raw_pred = MODEL.predict(X)

        pred = _predict_post_process(raw_pred, capacity if capacity > 0 else None)

        return jsonify(
            {
                "station_id": station_id,
                "datetime": target_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "features": _effective_model_features(),
                "feature_values": row,
                "weather_source": {
                    "mode": "db_only_fallback" if weather_fallback else "forecast",
                    "selected_forecast_time": weather.get("forecast_time") if weather else None,
                },
                "raw_pred": raw_pred.tolist(),
                "pred_available_bikes": pred.tolist(),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
