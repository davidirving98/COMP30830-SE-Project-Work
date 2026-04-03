from flask import Flask, request, jsonify
from datetime import datetime
import numpy as np

def fetch_openweather_forecast(date):
    # Stub: Replace with code to fetch weather forecast from OpenWeather
    return {
        "station_id": 32,
        "temperature": 20,
        "humidity": 60,
        "wind_speed": 5,
        "precipitation": 0
    }

# Initialize Flask app
app = Flask(__name__)

# Define a route for predictions
@app.route("/predict", methods=["GET"])
def predict():
    try:
        # Get date and time from request
        date = request.args.get("date")
        time = request.args.get("time")
        station_id = request.args.get("station_id")  #station_id as an input parameter
        
        if not date or not time or not station_id:
            return jsonify({"error": "Missing date, time, or station_id parameter"}), 400

        openweather_data = fetch_openweather_forecast(date)

        # Combine date and time into a single datetime object
        dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
        hour = dt.hour
        day_of_week = dt.weekday()

        # Combine data into input features
        input_features = [
            station_id,
            openweather_data["temperature"],
            openweather_data["humidity"],
            openweather_data["wind_speed"],
            openweather_data["precipitation"],
            hour,
            day_of_week,
        ]
        input_array = np.array(input_features).reshape(1, -1)

        # Make a prediction
        prediction = model.predict(input_array)
        
        return jsonify({"predicted_available_bikes": prediction[0]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
