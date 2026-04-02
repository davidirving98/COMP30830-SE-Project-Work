from flask import Flask, jsonify, render_template, request

import requests
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

from jcdecaux import get_stations, get_station, fetch_stations_raw
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
MODEL_PATH = PROJECT_ROOT / "machine_learning" / "linear_regression_lag_model.joblib"
META_PATH = PROJECT_ROOT / "machine_learning" / "linear_regression_lag_model_meta.joblib"

MODEL = None
MODEL_FEATURES = []
MODEL_TARGET = "available_bikes"

try:
    MODEL = joblib.load(MODEL_PATH)
    meta = joblib.load(META_PATH)
    MODEL_FEATURES = list(meta.get("features", []))
    MODEL_TARGET = str(meta.get("target", MODEL_TARGET))
except Exception:
    # Keep app bootable even when model artifacts are missing.
    MODEL = None
    MODEL_FEATURES = []


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

        missing = [c for c in MODEL_FEATURES if c not in df.columns]
        if missing:
            return jsonify({"error": f"Missing features: {missing}"}), 400

        X = df[MODEL_FEATURES]
        raw_pred = MODEL.predict(X)

        #  post-processing:
        # 1) avoid false positive dispatch: prediction < 3 => 0
        pred = np.where(raw_pred < 3, 0, raw_pred)

        # 2) keep prediction in [0, capacity] if capacity is provided
        if "capacity" in df.columns:
            pred = np.clip(pred, 0, df["capacity"].to_numpy())
        else:
            pred = np.clip(pred, 0, None)

        pred = np.rint(pred).astype(int)

        return jsonify(
            {
                "target": MODEL_TARGET,
                "features": MODEL_FEATURES,
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

        station_id = int(request.args["station_id"])
        target_dt = datetime.strptime(request.args["datetime"], "%Y-%m-%d %H:%M:%S")

        db_feat = get_prediction_db_features(station_id, target_dt)
        if not db_feat:
            return jsonify({"error": f"Station {station_id} not found"}), 404

        forecast_rows = get_forecast(full_series=True)
        weather = _pick_forecast_for_target(target_dt, forecast_rows)
        capacity = float(db_feat.get("capacity") or 0)
        humidity_bin = 1 if float(weather.get("humidity") or 0) > 90 else 0

        row = {
            "number": int(db_feat.get("number", station_id)),
            "capacity": capacity,
            "day": int(target_dt.day),
            "hour": int(target_dt.hour),
            "minute": int(target_dt.minute),
            "temp": float(weather.get("temperature")),
            "pressure": float(weather.get("pressure")),
            "humidity": int(humidity_bin),
            "lng": float(db_feat.get("lng")),
            "lat": float(db_feat.get("lat")),
            "bikes_1d_mean": float(db_feat.get("bikes_1d_mean") or 0),
            "bikes_same_slot_mean": float(db_feat.get("bikes_same_slot_mean") or 0),
        }

        X = pd.DataFrame([row])[MODEL_FEATURES]
        raw_pred = MODEL.predict(X)

        # Prediction limit to avoid false positive dispatch and availability qty over capacity .
        pred = np.where(raw_pred < 3, 0, raw_pred)
        pred = np.clip(pred, 0, capacity if capacity > 0 else None)
        pred = np.rint(pred).astype(int)

        return jsonify(
            {
                "station_id": station_id,
                "datetime": target_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "features": MODEL_FEATURES,
                "feature_values": row,
                "weather_source": {
                    "mode": "forecast",
                    "selected_forecast_time": weather.get("forecast_time"),
                },
                "raw_pred": raw_pred.tolist(),
                "pred_available_bikes": pred.tolist(),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
