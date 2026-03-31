import matplotlib.pyplot as plt
import pandas as pd
from sktime.datasets import load_airline
from sktime.forecasting.base import ForecastingHorizon
from sktime.forecasting.model_selection import temporal_train_test_split
from sktime.forecasting.ets import AutoETS
from sktime.performance_metrics.forecasting import mean_absolute_percentage_error

# Load dataset
y = load_airline()

# Ensure the index has a frequency
y.index = pd.PeriodIndex(y.index, freq="M")  # Convert index to PeriodIndex with monthly frequency

# Split data into train and test sets (last 36 months as test)
y_train, y_test = temporal_train_test_split(y, test_size=36)

# Initialize and fit AutoETS forecaster with automatic model selection
forecaster = AutoETS(auto=True, sp=12, n_jobs=-1)
forecaster.fit(y_train)

# Create forecasting horizon using test set indices
fh = ForecastingHorizon(y_test.index, is_relative=False)

# Generate forecasts
y_pred = forecaster.predict(fh)

# Calculate evaluation metric
mape = mean_absolute_percentage_error(y_test, y_pred)

# **Ensure indices are converted to DatetimeIndex for plotting**
y_train.index = y_train.index.to_timestamp()
y_test.index = y_test.index.to_timestamp()
y_pred.index = y_pred.index.to_timestamp()

# Plot results
plt.figure(figsize=(10, 6))
plt.plot(y_train.index, y_train, label='Training Data', color='blue')
plt.plot(y_test.index, y_test, label='Actual Values', color='green')
plt.plot(y_test.index, y_pred, label='Forecast', color='red')
plt.title(f'Airline Passengers Forecast (MAPE: {mape:.2%})')
plt.xlabel('Year')
plt.ylabel('Passengers')
plt.legend()
plt.grid(True)
plt.show()
