import os
from pathlib import Path

# Switch with env var: DB_ENV=local or DB_ENV=aws
DB_ENV = os.getenv("DB_ENV", "local").lower()

DB_CONFIGS = {
    "local": {
        "DB_HOST": "localhost",
        "DB_PORT": 3306,
        "DB_USER": "root",
        "DB_PASSWORD": "w20050718",
        "DB_NAME": "COMP30830_SW",
        "DB_SSLMODE": "prefer",
    },
    "aws": {
        "DB_HOST": "database-1.cn2ekioaaw47.eu-west-1.rds.amazonaws.com",
        "DB_PORT": 5432,
        "DB_USER": "alex",
        "DB_PASSWORD": "gojra6-kufwUz-qemvyj",
        "DB_NAME": "postgres",
        "DB_SSLMODE": "require",
    },
}

if DB_ENV not in DB_CONFIGS:
    raise ValueError(f"Invalid DB_ENV '{DB_ENV}'. Use 'local' or 'aws'.")

DB_HOST = DB_CONFIGS[DB_ENV]["DB_HOST"]
DB_PORT = DB_CONFIGS[DB_ENV]["DB_PORT"]
DB_USER = DB_CONFIGS[DB_ENV]["DB_USER"]
DB_PASSWORD = DB_CONFIGS[DB_ENV]["DB_PASSWORD"]
DB_NAME = DB_CONFIGS[DB_ENV]["DB_NAME"]
DB_SSLMODE = DB_CONFIGS[DB_ENV]["DB_SSLMODE"]

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "bikeinfo" / "data"

# JCDecaux API configuration
BIKE_API_KEY = "11c0b077ab18a5d4f761dc7b7469d89b7f5e22b3"
BIKE_STATUS_URL = (
    f"https://api.jcdecaux.com/vls/v1/stations?contract=dublin&apiKey={BIKE_API_KEY}"
)

# OpenWeather API configuration
OPENWEATHER_API_KEY = "3fcb7eb671157a29578b8e44f5ff4beb"
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
OPENWEATHER_CURRENT_URL = f"{OPENWEATHER_BASE_URL}/weather"
OPENWEATHER_FORECAST_URL = f"{OPENWEATHER_BASE_URL}/forecast"

# Optional local data paths
FOLDER_PATH = str(DATA_DIR / "dublinbike_status")
OPENWEATHER_FOLDER_PATH = str(DATA_DIR / "openweather")
