import requests
from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
import sqlalchemy as sqla
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config.py"
if not CONFIG_PATH.exists():
    raise FileNotFoundError(f"Missing config file: {CONFIG_PATH}")
print(f"Using config file: {CONFIG_PATH}", flush=True)
_spec = spec_from_file_location("project_config", CONFIG_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load config from: {CONFIG_PATH}")
config = module_from_spec(_spec)
_spec.loader.exec_module(config)

# pull in data from API and insert into database.
DB_NAME = getattr(config, "DB_NAME", "COMP30830_SW")
engine = sqla.create_engine(
    f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}"
    f"@{config.DB_HOST}:{getattr(config, 'DB_PORT', 3306)}/{DB_NAME}"
)

# Execute one pull + insert
resp = requests.get(config.BIKE_STATUS_URL, timeout=20)
resp.raise_for_status()
data = resp.json()  # Here we assume the top level is a list

station_rows = {}
availability_rows = []

for s in data:
    number = s.get("number") #primary key for station and foreign key for availability, so if missing just drop the record
    if number is None:
        continue

    station_rows[number] = {
        "number": number,
        "contract_name": s.get("contract_name"),
        "name": s.get("name"),
        "address": s.get("address"),
        "lat": (s.get("position") or {}).get("lat"),
        "lng": (s.get("position") or {}).get("lng"),
        "banking": bool(s.get("banking")),
        "bonus": bool(s.get("bonus")),
        "bike_stands": s.get("bike_stands"),
    }

    last_update_ms = s.get("last_update")
    last_update_dt = None
    if last_update_ms:
        last_update_dt = datetime.fromtimestamp(last_update_ms / 1000, tz=timezone.utc)

    availability_rows.append({
        "number": number,
        "available_bike_stands": s.get("available_bike_stands"),
        "available_bikes": s.get("available_bikes"),
        "status": s.get("status"),
        "last_update": last_update_dt,
    })

station_insert = sqla.text("""
INSERT INTO station (number, contract_name, name, address, lat, lng, banking, bonus, bike_stands)
VALUES (:number, :contract_name, :name, :address, :lat, :lng, :banking, :bonus, :bike_stands)
ON DUPLICATE KEY UPDATE
    contract_name = VALUES(contract_name),
    name = VALUES(name),
    address = VALUES(address),
    lat = VALUES(lat),
    lng = VALUES(lng),
    banking = VALUES(banking),
    bonus = VALUES(bonus),
    bike_stands = VALUES(bike_stands);
""")

availability_insert = sqla.text("""
INSERT INTO availability (number, available_bike_stands, available_bikes, status, last_update)
VALUES (:number, :available_bike_stands, :available_bikes, :status, :last_update)
ON DUPLICATE KEY UPDATE
    available_bike_stands = VALUES(available_bike_stands),
    available_bikes = VALUES(available_bikes),
    status = VALUES(status);
""")

with engine.begin() as conn:
    conn.execute(station_insert, list(station_rows.values()))
    conn.execute(availability_insert, availability_rows)

print(f"API import completed: stations={len(station_rows)}, availability={len(availability_rows)}", flush=True)
