import os
from pathlib import Path


def _load_env_file(env_path: Path):
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


BASE_DIR = Path(__file__).resolve().parent
_load_env_file(BASE_DIR / ".env")

# Switch with env var: DB_ENV=local or DB_ENV=aws
DB_ENV = os.getenv("DB_ENV", "local").lower()

DB_CONFIGS = {
    "local": {
        "DB_HOST": "127.0.0.1",
        "DB_PORT": 3306,
        "DB_USER": "root",
        "DB_PASSWORD": "",
        "DB_NAME": "COMP30830_SW",
        "DB_SSLMODE": "prefer",
    },
    "aws": {
        "DB_HOST": "",
        "DB_PORT": 5432,
        "DB_USER": "",
        "DB_PASSWORD": "",
        "DB_NAME": "",
        "DB_SSLMODE": "require",
    },
}

if DB_ENV not in DB_CONFIGS:
    raise ValueError(f"Invalid DB_ENV '{DB_ENV}'. Use 'local' or 'aws'.")

ENV_PREFIX = "LOCAL" if DB_ENV == "local" else "AWS"

DB_HOST = os.getenv(f"{ENV_PREFIX}_DB_HOST", DB_CONFIGS[DB_ENV]["DB_HOST"])
DB_PORT = int(os.getenv(f"{ENV_PREFIX}_DB_PORT", DB_CONFIGS[DB_ENV]["DB_PORT"]))
DB_USER = os.getenv(f"{ENV_PREFIX}_DB_USER", DB_CONFIGS[DB_ENV]["DB_USER"])
DB_PASSWORD = os.getenv(
    f"{ENV_PREFIX}_DB_PASSWORD", DB_CONFIGS[DB_ENV]["DB_PASSWORD"]
)
DB_NAME = os.getenv(f"{ENV_PREFIX}_DB_NAME", DB_CONFIGS[DB_ENV]["DB_NAME"])
DB_SSLMODE = os.getenv(f"{ENV_PREFIX}_DB_SSLMODE", DB_CONFIGS[DB_ENV]["DB_SSLMODE"])

# Base paths
DATA_DIR = BASE_DIR / "bikeinfo" / "data"

# JCDecaux API configuration
BIKE_API_KEY = os.getenv("BIKE_API_KEY", "")
BIKE_STATUS_URL = (
    f"https://api.jcdecaux.com/vls/v1/stations?contract=dublin&apiKey={BIKE_API_KEY}"
)

# OpenWeather API configuration
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
OPENWEATHER_CURRENT_URL = f"{OPENWEATHER_BASE_URL}/weather"
OPENWEATHER_FORECAST_URL = f"{OPENWEATHER_BASE_URL}/forecast"

# Optional local data paths
FOLDER_PATH = str(DATA_DIR / "dublinbike_status")
OPENWEATHER_FOLDER_PATH = str(DATA_DIR / "openweather")
