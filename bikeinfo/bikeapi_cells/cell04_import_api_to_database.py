import requests
from datetime import datetime, timezone
import sqlalchemy as sqla
from pathlib import Path
import sys

BIKEINFO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BIKEINFO_DIR))
import config

# pull in data from API and insert into database.
DB_NAME = getattr(config, "DB_NAME", "postgres")
engine = sqla.create_engine(
    f"postgresql+psycopg2://{config.DB_USER}:{config.DB_PASSWORD}"
    f"@{config.DB_HOST}:{getattr(config, 'DB_PORT', 5432)}/{DB_NAME}"
    f"?sslmode={getattr(config, 'DB_SSLMODE', 'require')}"
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
ON CONFLICT (number) DO UPDATE SET
    contract_name = EXCLUDED.contract_name,
    name = EXCLUDED.name,
    address = EXCLUDED.address,
    lat = EXCLUDED.lat,
    lng = EXCLUDED.lng,
    banking = EXCLUDED.banking,
    bonus = EXCLUDED.bonus,
    bike_stands = EXCLUDED.bike_stands;
""")

availability_insert = sqla.text("""
INSERT INTO availability (number, available_bike_stands, available_bikes, status, last_update)
VALUES (:number, :available_bike_stands, :available_bikes, :status, :last_update);
""")

with engine.begin() as conn:
    conn.execute(station_insert, list(station_rows.values()))
    conn.execute(availability_insert, availability_rows)

print(f"API import completed: stations={len(station_rows)}, availability={len(availability_rows)}", flush=True)
