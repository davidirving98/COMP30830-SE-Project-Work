import pandas as pd
import pickle

# Load the saved model
with open("bike_availability_model.pkl", "rb") as file:
    model = pickle.load(file)

# Define new input data for prediction
new_data = pd.DataFrame({
    'station_id': [32],
    'temperature': [20],
    'humidity': [60],
    'wind_speed': [10],
    'precipitation': [0],
    'hour': [9],
    'day_of_week': [2]  # Example: 0 = Monday, 1 = Tuesday, etc.
})

# Make prediction
prediction = model.predict(new_data)
# Output prediction
print(f"Predicted number of available bikes: {prediction[0]}")

