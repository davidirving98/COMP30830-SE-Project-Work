from flask import Flask, jsonify, render_template, request

import logging
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
    get_latest_stations_view,)

from ml_service import (
    parse_predict_query_args,
    predict_by_station_and_datetime,
    predict_from_payload,)

app = Flask(__name__)
logger = logging.getLogger("backend")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] action=%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False
# Keep backend logs minimal: action + result only.
logging.getLogger("werkzeug").setLevel(logging.ERROR)


def log_action(action: str, result: str):
    logger.info(f"{action} result={result}")


def refresh_stations_on_startup():
    # Refresh station snapshot once when Flask process starts.
    data = fetch_stations_raw()
    if data is None:
        log_action("startup.stations_refresh", "skipped_bike_api_unavailable")
        return
    result = save_snapshot(data)
    log_action("startup.stations_refresh", f"ok details={result}")

# The following endpoints are for the main API functionality, serving data to the frontend and providing a manual refresh option for bike station data.
@app.route("/")
def index():
    return render_template("index.html", apikey=config.GOOGLE_MAPS_API_KEY)


@app.route("/stations")
def stations():
    try:
        # Read latest snapshot from DB only.
        # API polling is handled by the background importer (cell04).
        data = get_latest_stations_view()
        log_action("stations.list", "ok")
        return jsonify(data)
    except Exception as e:
        log_action("stations.list", "error")
        return jsonify({"error": f"/stations failed: {str(e)}"}), 500


@app.route("/stations/refresh") # Manual refresh endpoint: fetch from API and persist now. Frontend can call this if they want to force an update outside of the regular polling schedule.
def stations_refresh():
    # Manual fallback endpoint: fetch from API and persist now.
    data = fetch_stations_raw()
    if data is None:
        log_action("stations.refresh", "error_bike_api_unavailable")
        return jsonify({"error": "Bike API unavailable"}), 500
    result = save_snapshot(data)
    log_action("stations.refresh", "ok")
    return jsonify(result)


@app.route("/weather") # 前端调用此接口获取当前天气数据。
def weather():
    data = get_weather()
    if data is None:
        log_action("weather.current", "error_weather_api_unavailable")
        return jsonify({"error": "Weather API unavailable"}), 500
    log_action("weather.current", "ok")
    return jsonify(data)


@app.route("/forecast") # 前端调用此接口获取天气预报数据。
def forecast():
    data = get_forecast()

    if data is None:
        log_action("weather.forecast", "error_forecast_api_unavailable")
        return jsonify({"error": "Forecast API unavailable"}), 500

    log_action("weather.forecast", "ok")
    return jsonify(data)

#调试代码,已经通过,暂时保留
# @app.route("/station/<int:station_id>/info")
# def station_info(station_id):

#     station = get_station(station_id)
#     weather = get_weather()

#     if station is None or weather is None:
#         return jsonify({"error": "Data unavailable"}), 500

#     return jsonify({"station": station, "weather": weather})


# The following endpoints are for testing the SQL database connection and queries.
# @app.route("/stations_SQL")
# def stations_sql():
#     try:
#         return jsonify(get_stations_sql())
#     except Exception as e:
#         return jsonify({"error": f"Data not found: {str(e)}"}), 500


# # This endpoint returns the current availability of bikes and stands for all stations.
# @app.route("/availability_SQL")
# def availability_sql():
#     try:
#         return jsonify(get_availability_sql())
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# # This endpoint returns detailed information about a specific station
# @app.route("/stations_SQL/<int:station_id>/info")
# def station_sql_info(station_id):
#     try:
#         station = get_station_sql(station_id)
#         if station is None:
#             return jsonify({"error": "Station not found"}), 404
#         return jsonify(station)
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# This endpoint returns the historical availability data for a specific station.
@app.route("/station/<int:station_id>/history") # front end shows historical data charts by calling this endpoint with station_id as path parameter.
def station_history(station_id):
    try:
        data = get_station_history_sql(station_id)
        log_action("station.history", "ok")
        return jsonify(data)
    except Exception as e:
        log_action("station.history", "error")
        return jsonify({"error": str(e)}), 500



@app.route("/predict", methods=["POST"]) # test endpoint, not used by frontend
def predict():

    try:
        payload = request.get_json(force=True, silent=True)
        data, status = predict_from_payload(payload)
        log_action("predict.payload", "ok" if status < 400 else "error")
        return jsonify(data), status
    except Exception as e:
        log_action("predict.payload", "error")
        return jsonify({"error": str(e)}), 500


@app.route("/predict/by-input", methods=["GET"]) # fronted 调用此接口，传入 station_id 和 datetime 作为查询参数，返回预测结果。
def predict_by_input():
    try:
        station_id, target_dt, err = parse_predict_query_args(request.args)
        if err:
            data, status = err
            log_action("predict.by_input", "error_invalid_query")
            return jsonify(data), status

        data, status = predict_by_station_and_datetime(station_id, target_dt)
        log_action("predict.by_input", "ok" if status < 400 else "error")
        return jsonify(data), status
    except Exception as e:
        log_action("predict.by_input", "error")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    refresh_stations_on_startup()
    app.run(host="0.0.0.0", port=port, debug=False)
