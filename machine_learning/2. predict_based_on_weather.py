import pandas as pd
import pickle
from datetime import datetime

# Load the trained model
with open("bike_availability_model.pkl", "rb") as file:
    model = pickle.load(file)

MODEL_FEATURES = list(model.feature_names_in_) if hasattr(model, "feature_names_in_") else []

station_meta = (
    pd.read_csv("final_merged_data.csv", usecols=["station_id", "lat", "lon", "capacity"])
    .dropna()
    .drop_duplicates(subset=["station_id"])
)

def get_weather_forecast(city, date):
    """Stub function for weather forecast. Returns fixed weather data: REPLACE WITH CALL TO OPENWEATHER API
    """
    return {
        'relative_humidity_percent': 60.0,
        'min_air_temperature_celsius': 14.0,
        'max_air_temperature_celsius': 20.0,
    }

def predict_bike_availability(station_id, city, date_str, time_str):
    """Predict the number of available bikes for a given city, date, and time."""
    # Parse input date and time
    date_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    hour = date_time.hour
    minute = date_time.minute
    weekday = date_time.weekday()
    day = date_time.day
    month = date_time.month

    row = station_meta.loc[station_meta["station_id"] == station_id]
    if row.empty:
        raise ValueError(f"station_id {station_id} not found in station metadata")
    row = row.iloc[0]

    # Use the function for weather forecast
    weather_features = get_weather_forecast(city, date_str)
    humidity = weather_features['relative_humidity_percent']
    avg_temp = (
        weather_features['min_air_temperature_celsius']
        + weather_features['max_air_temperature_celsius']
    ) / 2.0
    
    # Prepare input data for the model
    input_data = pd.DataFrame([{
        'station_id': station_id,
        'lat': float(row['lat']),
        'lon': float(row['lon']),
        'capacity': float(row['capacity']),
        'month': month,
        'day': day,
        'hour': hour,
        'minute': minute,
        'relative_humidity_percent': humidity,
        'peak_time_weekday': int((weekday < 5) and (hour in [7, 8, 9, 16, 17, 18, 19])),
        'peak_time_weekend': int((weekday >= 5) and (11 <= hour <= 17)),
        'likely_wet': int(humidity > 70),
        'likely_dry': int(humidity < 40),
        'average_temperature_celsius': avg_temp,
    }])

    if MODEL_FEATURES:
        input_data = input_data[MODEL_FEATURES]

    # Make prediction
    prediction = model.predict(input_data)
    return prediction[0]

# Example usage
city = "Dublin"
date_str = "2024-02-25"
time_str = "09:00"
station_id = 32

predicted_bikes = predict_bike_availability(
    station_id,
    city,
    date_str,
    time_str,
)
print(f"Predicted number of available bikes in {city} on {date_str} at {time_str}: {predicted_bikes}")
