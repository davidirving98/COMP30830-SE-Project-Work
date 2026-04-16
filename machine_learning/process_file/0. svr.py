import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.svm import SVR
from sklearn.svm import LinearSVR
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
import joblib
import pickle

INTERVALS_PER_DAY = 144   # 10-min granularity
INTERVALS_PER_WEEK = 1008 # 7 * 144

# Load the dataset
data = pd.read_csv("final_merged_data.csv.gz")

# Parse timestamp and keep valid rows
data['last_reported'] = pd.to_datetime(data['last_reported'], errors='coerce')
data.dropna(subset=['last_reported', 'station_id', 'num_bikes_available'], inplace=True)

# Use original time features from source columns (not derived from last_reported)
for c in ['day', 'hour', 'minute']:
    if c not in data.columns:
        raise KeyError(f"Missing required time column: {c}")
    data[c] = pd.to_numeric(data[c], errors='coerce')
data.dropna(subset=['day', 'hour', 'minute'], inplace=True)
data['day'] = data['day'].astype(int)
data['hour'] = data['hour'].astype(int)
data['minute'] = data['minute'].astype(int)

# Cyclical encoding for hour and day
data['hour_sin'] = np.sin(2 * np.pi * data['hour'] / 24)
data['hour_cos'] = np.cos(2 * np.pi * data['hour'] / 24)
data['day_sin'] = np.sin(2 * np.pi * (data['day'] - 1) / 31)
data['day_cos'] = np.cos(2 * np.pi * (data['day'] - 1) / 31)

# Temperature mean
if 'max_air_temperature_celsius' not in data.columns or 'min_air_temperature_celsius' not in data.columns:
    raise KeyError("Missing required temperature columns: max_air_temperature_celsius, min_air_temperature_celsius")
data['average_temperature_celsius'] = (
    data['max_air_temperature_celsius'] + data['min_air_temperature_celsius']
) / 2.0

# Pressure mean
if 'max_barometric_pressure_hpa' not in data.columns or 'min_barometric_pressure_hpa' not in data.columns:
    raise KeyError("Missing required pressure columns: max_barometric_pressure_hpa, min_barometric_pressure_hpa")
data['average_pressure_hpa'] = (
    data['max_barometric_pressure_hpa'] + data['min_barometric_pressure_hpa']
) / 2.0

# Humidity categories from humidity mean
if 'max_relative_humidity_percent' not in data.columns or 'min_relative_humidity_percent' not in data.columns:
    raise KeyError("Missing required humidity columns: max_relative_humidity_percent, min_relative_humidity_percent")
data['average_humidity_percent'] = (
    data['max_relative_humidity_percent'] + data['min_relative_humidity_percent']
) / 2.0

data['likely_wet'] = (data['average_humidity_percent'] > 70).astype(int)
data['likely_dry'] = (data['average_humidity_percent'] < 40).astype(int)

# Lag features (avoid leakage by shift(1))
data = data.sort_values(['station_id', 'last_reported']).reset_index(drop=True)
by_station = data.groupby('station_id')['num_bikes_available']

data['bikes_1d_mean'] = by_station.transform(
    lambda s: s.shift(1).rolling(INTERVALS_PER_DAY, min_periods=INTERVALS_PER_DAY // 2).mean()
)
data['bikes_7d_mean'] = by_station.transform(
    lambda s: s.shift(1).rolling(INTERVALS_PER_WEEK, min_periods=INTERVALS_PER_DAY).mean()
)
data['bikes_7d_std'] = by_station.transform(
    lambda s: s.shift(1).rolling(INTERVALS_PER_WEEK, min_periods=INTERVALS_PER_DAY).std()
)
data['bikes_same_slot_prev_day'] = by_station.shift(INTERVALS_PER_DAY)
data['bikes_same_slot_prev_week'] = by_station.shift(INTERVALS_PER_WEEK)

# Track whether previous-week same slot exists
# (1 = real history exists, 0 = imputed)
data['has_prev_week'] = data['bikes_same_slot_prev_week'].notna().astype(int)

# Fill lag NaNs using station mean target, then global mean as fallback
station_mean_target = data.groupby('station_id')['num_bikes_available'].transform('mean')
global_mean_target = float(data['num_bikes_available'].mean())
lag_cols = [
    'bikes_1d_mean',
    'bikes_7d_mean',
    'bikes_7d_std',
    'bikes_same_slot_prev_day',
    'bikes_same_slot_prev_week',
]
for col in lag_cols:
    data[col] = data[col].fillna(station_mean_target).fillna(global_mean_target)

# Define features and target
features = [
    'station_id',
    'lat',
    'lon',
    'capacity',
    'day_sin',
    'day_cos',
    'hour_sin',
    'hour_cos',
    'minute',
    'likely_wet',
    'likely_dry',
    'average_temperature_celsius',
    'average_pressure_hpa',
    'bikes_1d_mean',
    'bikes_7d_mean',
    'bikes_7d_std',
    'bikes_same_slot_prev_day',
    'bikes_same_slot_prev_week',
    'has_prev_week',
]
target = 'num_bikes_available'

missing_cols = [col for col in features + [target] if col not in data.columns]
if missing_cols:
    raise KeyError(f"Missing columns in final_merged_data.csv: {missing_cols}")

data.dropna(subset=features + [target], inplace=True)

# Split by time order: earlier timestamps for training, later timestamps for testing
data.sort_values('last_reported', inplace=True)
data.reset_index(drop=True, inplace=True)
data.drop(columns=['last_reported'], inplace=True)

# Reduce precision for compact storage/training memory
# 1) Safe integer downcast to uint8
uint8_cols = [
    'station_id',
    'capacity',
    'day',
    'minute',
    'likely_wet',
    'likely_dry',
    'has_prev_week',
    'num_bikes_available',
]
for c in uint8_cols:
    if c in data.columns:
        data[c] = data[c].astype('uint8')

# 2) float64 -> float32 for all float columns
float_cols = data.select_dtypes(include=['float64']).columns
if len(float_cols) > 0:
    data[float_cols] = data[float_cols].astype('float32')

categorical_features = ['station_id']
numeric_features = [col for col in features if col not in categorical_features]

preprocessor = ColumnTransformer([
    ('station_ohe', OneHotEncoder(handle_unknown='ignore'), categorical_features),
    ('num', StandardScaler(), numeric_features),
])

model = Pipeline([
    ('preprocess', preprocessor),
    ('regressor', LinearSVR(max_iter=10000, C=1.0, epsilon=0.1))
])

X_all = data[features]
y_all = data[target]

# 5-fold cross validation for time series
cv = TimeSeriesSplit(n_splits=5)
cv_r2_scores = cross_val_score(model, X_all, y_all, cv=cv, scoring='r2')
cv_mae_scores = -cross_val_score(model, X_all, y_all, cv=cv, scoring='neg_mean_absolute_error')

print(f"CV(5)-MAE Mean: {cv_mae_scores.mean()}")
print(f"CV(5)-R² Mean: {cv_r2_scores.mean()}")

# 70/30 time-based split
split_idx = int(len(data) * 0.7)
if split_idx == 0 or split_idx == len(data):
    raise ValueError("Not enough data to perform time-based split with 70/30 ratio.")

train_data = data.iloc[:split_idx]
test_data = data.iloc[split_idx:]

X_train = train_data[features]
y_train = train_data[target]
X_test = test_data[features]
y_test = test_data[target]

# Train and evaluate
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
print(f"Mean Absolute Error: {mae}")
print(f"R² Score: {r2}")

# Display model coefficients
regressor = model.named_steps['regressor']

if hasattr(regressor, "coef_"):
    print("\nModel Coefficients:")
    feature_names = model.named_steps['preprocess'].get_feature_names_out()
    coefs = regressor.coef_
    for feature, coef in zip(feature_names, coefs):
        print(f"{feature}: {coef}")
    print(f"Intercept: {regressor.intercept_}")

elif hasattr(regressor, "feature_importances_"):
    print("\nFeature Importances:")
    feature_names = model.named_steps['preprocess'].get_feature_names_out()
    importances = regressor.feature_importances_
    for feature, imp in zip(feature_names, importances):
        print(f"{feature}: {imp}")

else:
    print("\nModel does not provide coefficients or feature importances.")

# Save model files
model_filename = "svr_model.joblib"
joblib.dump(model, model_filename)
print(f"Model saved to {model_filename}")

model_filename = "svr_model.pkl"
with open(model_filename, "wb") as file:
    pickle.dump(model, file)
print(f"Model saved to {model_filename}")
