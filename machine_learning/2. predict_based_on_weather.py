import pandas as pd
import pickle
from datetime import datetime

# Load the trained model
with open("bike_availability_model.pkl", "rb") as file:
    model = pickle.load(file)

def get_weather_forecast(city, date):
    """Stub function for weather forecast. Returns fixed weather data: REPLACE WITH CALL TO OPENWEATHER API
    """
    return {
        'temperature': 20.0,
        'humidity': 60.0,
        'wind_speed': 10.0,
        'precipitation': 0.0
    }

def predict_bike_availability(station_id, city, date_str, time_str):
    """Predict the number of available bikes for a given city, date, and time."""
    # Parse input date and time
    date_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    hour = date_time.hour
    day_of_week = date_time.weekday()

    # Use the function for weather forecast
    weather_features = get_weather_forecast(city, date_str)
    
    # Prepare input data for the model
    input_data = pd.DataFrame([{
        'station_id': station_id,
        'temperature': weather_features['temperature'],
        'humidity': weather_features['humidity'],
        'wind_speed': weather_features['wind_speed'],
        'precipitation': weather_features['precipitation'],
        'hour': hour,
        'day_of_week': day_of_week
    }])

    # Make prediction
    prediction = model.predict(input_data)
    return prediction[0]

# Example usage
station_id = 1  # Example station ID
city = "Dublin"
date_str = "2024-02-25"
time_str = "09:00"

predicted_bikes = predict_bike_availability(station_id, city, date_str, time_str)
print(f"Predicted number of available bikes in {city} on {date_str} at {time_str}: {predicted_bikes}")
