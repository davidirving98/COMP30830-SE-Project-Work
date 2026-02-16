# Database Configuration (PostgreSQL / RDS)
import os
from pathlib import Path

DB_HOST = "database-1.cn2ekioaaw47.eu-west-1.rds.amazonaws.com"
DB_PORT = 5432
DB_USER = "alex"
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = "postgres"
DB_SSLMODE = "require"

# Base Path
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Dublin Bike API Configuration
BIKE_API_KEY = "11c0b077ab18a5d4f761dc7b7469d89b7f5e22b3"
BIKE_STATUS_URL = (
    f"https://api.jcdecaux.com/vls/v1/stations?contract=dublin&apiKey={BIKE_API_KEY}"
)

# OpenWeather API Configuration
OPENWEATHER_API_KEY = "3fcb7eb671157a29578b8e44f5ff4beb"
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
OPENWEATHER_CURRENT_URL = f"{OPENWEATHER_BASE_URL}/weather"
OPENWEATHER_FORECAST_URL = f"{OPENWEATHER_BASE_URL}/forecast"

# Data Path Configuration
FOLDER_PATH = str(DATA_DIR / "dublinbike_status")
OPENWEATHER_FOLDER_PATH = str(DATA_DIR / "openweather")
# modified on 2.16
