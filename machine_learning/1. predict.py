import pandas as pd
import pickle
from datetime import datetime

# Load the saved model
with open("bike_availability_model.pkl", "rb") as file:
    model = pickle.load(file)

required_features = list(model.feature_names_in_) if hasattr(model, "feature_names_in_") else None

# Define new input data for prediction
dt = datetime.strptime("2024-03-15 09:00", "%Y-%m-%d %H:%M")
hour = dt.hour
minute = dt.minute
weekday = dt.weekday()
humidity = 60.0
new_data = pd.DataFrame({
    'station_id': [32],
    'lat': [53.3498],
    'lon': [-6.2603],
    'capacity': [30],
    'month': [3],
    'day': [15],
    'hour': [hour],
    'minute': [minute],
    'relative_humidity_percent': [humidity],
    'peak_time_weekday': [int((weekday < 5) and (hour in [7, 8, 9, 16, 17, 18, 19]))],
    'peak_time_weekend': [int((weekday >= 5) and (11 <= hour <= 17))],
    'likely_wet': [int(humidity > 70)],
    'likely_dry': [int(humidity < 40)],
    'average_temperature_celsius': [(14.0 + 20.0) / 2.0],
})

if required_features is not None:
    missing = [col for col in required_features if col not in new_data.columns]
    if missing:
        raise ValueError(f"Missing required features for prediction: {missing}")
    new_data = new_data[required_features]

# Make prediction
prediction = model.predict(new_data)
# Output prediction
print(f"Predicted number of available bikes: {prediction[0]}")

