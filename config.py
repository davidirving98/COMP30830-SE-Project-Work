import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Database configuration (plaintext in config.py)
# Switch target with:
# 1) export DB_ENV=local|rds, or
# 2) change the default value below.
DB_ENV = os.getenv("DB_ENV", "local").lower()

DB_CONFIGS = {
    "local": {
        "DB_DIALECT": "mysql",
        "DB_HOST": "127.0.0.1",
        "DB_PORT": 3306,
        "DB_USER": "root",
        "DB_PASSWORD": "w20050718",
        "DB_NAME": "COMP30830_SW",
    },
    "rds": {
        "DB_DIALECT": "mysql",
        "DB_HOST": "database-2.cn2ekioaaw47.eu-west-1.rds.amazonaws.com",
        "DB_PORT": 3306,
        "DB_USER": "alex",
        "DB_PASSWORD": "gojra6-kufwUz-qemvyj",
        "DB_NAME": "mysql",
    },
}

if DB_ENV not in DB_CONFIGS:
    raise ValueError("DB_ENV must be 'local' or 'rds'")

_db = DB_CONFIGS[DB_ENV]
DB_DIALECT = _db["DB_DIALECT"]
DB_HOST = _db["DB_HOST"]
DB_PORT = _db["DB_PORT"]
DB_USER = _db["DB_USER"]
DB_PASSWORD = _db["DB_PASSWORD"]
DB_NAME = _db["DB_NAME"]

# Base paths
DATA_DIR = BASE_DIR / "bikeinfo" / "data"

# JCDecaux API configuration (read from OS environment variables)
JCDECAUX_API_KEY = os.getenv("JCDECAUX_API_KEY")
BIKE_CONTRACT = "dublin"
BIKE_STATUS_URL = None
if JCDECAUX_API_KEY:
    BIKE_STATUS_URL = (
        f"https://api.jcdecaux.com/vls/v1/stations"
        f"?contract={BIKE_CONTRACT}&apiKey={JCDECAUX_API_KEY}"
    )

# OpenWeather API configuration (read from OS environment variables)
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
OPENWEATHER_CURRENT_URL = f"{OPENWEATHER_BASE_URL}/weather"
OPENWEATHER_FORECAST_URL = f"{OPENWEATHER_BASE_URL}/forecast"
OPENWEATHER_CITY = "Dublin"

# Optional local data paths
FOLDER_PATH = str(DATA_DIR / "dublinbike_status")
OPENWEATHER_FOLDER_PATH = str(DATA_DIR / "openweather")
