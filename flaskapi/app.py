from flask import Flask, jsonify
import requests
from openweather import get_weather
from jcdecaux import get_stations, get_station

app = Flask(__name__)

@app.route("/")
def home():
    return "Bike + Weather API is running"

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

    return jsonify({
        "station": station,
        "weather": weather })

if __name__ == "__main__":
    app.run(host ="0.0.0.0", port=5000, debug=True)
