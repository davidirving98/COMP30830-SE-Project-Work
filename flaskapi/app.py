from flask import Flask, jsonify, request, render_template_string
import requests
from openweather import get_weather
from jcdecaux import get_stations, get_station


app = Flask(__name__)


# @app.route("/")
# def home():
#     return "Bike + Weather API is running"
@app.route("/")
def home():
    return render_template_string(
        """
    <h2>Bike API</h2>
    <p><a href="/stations_SQL">All stations on database</a></p>
    <p><a href="/availability_SQL">All availability database</a></p>

    <h3>Station Info</h3>
    <input id="sid" type="number" min="1" max="115" placeholder="station id (1-115)">
    <button onclick="go()">Go</button>

    <script>
      function go() {
        const id = Number(document.getElementById('sid').value);
        if (!Number.isInteger(id) || id < 1 || id > 115) {
          alert('station id must be between 1 and 115');
          return;
        }
        window.location.href = `/stations_SQL/${id}/info`;
      }
    </script>
    """
    )


@app.route("/stations")
def stations():
    data = get_stations()

    if data is None:
        return jsonify({"error": "Bike API unavailable"}), 500

    return jsonify(data)


@app.route("/weather")
def weather():
    data = get_weather()

    if data is None:
        return jsonify({"error": "Weather API unavailable"}), 500

    return jsonify(data)


@app.route("/station/<int:station_id>/info")
def station_info(station_id):

    station = get_station(station_id)
    weather = get_weather()

    if station is None or weather is None:
        return jsonify({"error": "Data unavailable"}), 500

    return jsonify({"station": station, "weather": weather})


from bikeinfo_SQL import (
    get_stations_sql,
    get_availability_sql,
    get_station_sql,
    search_stations_sql,
)


@app.route("/stations_SQL")
def stations_sql():
    try:
        return jsonify(get_stations_sql())
    except Exception as e:
        return jsonify({"error: data not found": str(e)}), 500


@app.route("/availability_SQL")
def availability_sql():
    try:
        return jsonify(get_availability_sql())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/stations_SQL/<int:station_id>/info")
def station_sql_info(station_id):
    try:
        station = get_station_sql(station_id)
        if station is None:
            return jsonify({"error": "Station not found"}), 404
        return jsonify(station)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
