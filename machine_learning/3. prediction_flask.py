from flask import Flask, request, jsonify
from datetime import datetime
import pandas as pd
import pickle

with open("bike_availability_model.pkl", "rb") as file:
    model = pickle.load(file)

MODEL_FEATURES = list(model.feature_names_in_) if hasattr(model, "feature_names_in_") else []

station_meta = (
    pd.read_csv("final_merged_data.csv", usecols=["station_id", "lat", "lon", "capacity"])
    .dropna()
    .drop_duplicates(subset=["station_id"])
)

def fetch_openweather_forecast(date):
    # Stub: Replace with code to fetch weather forecast from OpenWeather
    return {
        "relative_humidity_percent": 60,
        "min_air_temperature_celsius": 14,
        "max_air_temperature_celsius": 20,
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
        dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        hour = dt.hour
        minute = dt.minute
        weekday = dt.weekday()
        day = dt.day
        month = dt.month
        station_row = station_meta.loc[station_meta["station_id"] == int(station_id)]
        if station_row.empty:
            return jsonify({"error": f"station_id {station_id} not found"}), 400
        station_row = station_row.iloc[0]
        humidity = float(openweather_data["relative_humidity_percent"])
        avg_temp = (
            float(openweather_data["min_air_temperature_celsius"])
            + float(openweather_data["max_air_temperature_celsius"])
        ) / 2.0

        # Combine data into input features
        input_df = pd.DataFrame([{
            "station_id": int(station_id),
            "lat": float(station_row["lat"]),
            "lon": float(station_row["lon"]),
            "capacity": float(station_row["capacity"]),
            "month": month,
            "day": day,
            "hour": hour,
            "minute": minute,
            "relative_humidity_percent": humidity,
            "peak_time_weekday": int((weekday < 5) and (hour in [7, 8, 9, 16, 17, 18, 19])),
            "peak_time_weekend": int((weekday >= 5) and (11 <= hour <= 17)),
            "likely_wet": int(humidity > 70),
            "likely_dry": int(humidity < 40),
            "average_temperature_celsius": avg_temp,
        }])
        if MODEL_FEATURES:
            missing = [col for col in MODEL_FEATURES if col not in input_df.columns]
            if missing:
                return jsonify({"error": f"Missing required features: {missing}"}), 500
            input_df = input_df[MODEL_FEATURES]

        # Make a prediction
        prediction = model.predict(input_df)
        
        return jsonify({"predicted_available_bikes": prediction[0]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
