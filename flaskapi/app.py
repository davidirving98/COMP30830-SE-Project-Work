from flask import Flask, jsonify, render_template, request

import os
import sys
from pathlib import Path

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
    save_snapshot,
    get_latest_stations_view,
)
from ml_service import (
    parse_predict_query_args,
    predict_from_payload,
    predict_by_station_and_datetime,
)

app = Flask(__name__)


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
        payload = request.get_json(force=True, silent=True)
        data, status = predict_from_payload(payload)
        return jsonify(data), status
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/predict/by-input", methods=["GET"])
def predict_by_input():
    try:
        station_id, target_dt, err = parse_predict_query_args(request.args)
        if err:
            data, status = err
            return jsonify(data), status

        data, status = predict_by_station_and_datetime(station_id, target_dt)
        return jsonify(data), status
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    __import__("subprocess").Popen([sys.executable, str(PROJECT_ROOT / "bikeinfo" / "bikeapi_cells" / "cell04_import_api_to_database.py")], cwd=str(PROJECT_ROOT))
    app.run(host="0.0.0.0", port=port, debug=False)
