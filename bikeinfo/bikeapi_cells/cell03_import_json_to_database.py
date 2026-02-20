import json
from pathlib import Path
from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
import sqlalchemy as sqla

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

DB_NAME = getattr(config, "DB_NAME", "postgres")

# confirm connection to the new database
engine = sqla.create_engine(
    f"postgresql+psycopg2://{config.DB_USER}:{config.DB_PASSWORD}"
    f"@{config.DB_HOST}:{getattr(config, 'DB_PORT', 5432)}/{DB_NAME}"
    f"?sslmode={getattr(config, 'DB_SSLMODE', 'require')}"
)

# Create tables (station + availability)
create_station_sql = """
CREATE TABLE IF NOT EXISTS station (
    number INT PRIMARY KEY,
    contract_name VARCHAR(64),
    name VARCHAR(128),
    address VARCHAR(256),
    lat DECIMAL(9,6),
    lng DECIMAL(9,6),
    banking BOOLEAN,
    bonus BOOLEAN,
    bike_stands INT
);
"""

create_availability_sql = """
CREATE TABLE IF NOT EXISTS availability (
    id BIGSERIAL PRIMARY KEY,
    number INT NOT NULL,
    available_bike_stands INT,
    available_bikes INT,
    status VARCHAR(16),
    last_update TIMESTAMPTZ,
    CONSTRAINT fk_station_number
        FOREIGN KEY (number) REFERENCES station(number)
        ON DELETE CASCADE
);
"""

with engine.begin() as conn: #use SQLAlchemy's transaction context to ensure atomicity
    conn.execute(sqla.text(create_station_sql))
    conn.execute(sqla.text(create_availability_sql))
    conn.execute(sqla.text("CREATE INDEX IF NOT EXISTS idx_number_time ON availability (number, last_update)"))

print("Table structure confirmed", flush=True)

# Read local JSON files 
input_path = Path("data/dublinbike_status")

json_files = []
if input_path.is_dir():
    json_files = sorted(input_path.glob("station_status_*.json"))# only read files matching the pattern, and sort by name (timestamp)
else:
    json_files = [input_path] # if it's a single file, just put it in a list

print(f" Found {len(json_files)} files", flush=True)

# Insert data
station_rows = {} #use dict to deduplicate station info by number,should keep 115 records for the real stops
availability_rows = [] #keep all availability records, should be 115 * number of files
for fp in json_files:
    data = json.loads(fp.read_text(encoding="utf-8"))# read Json file by python function

    for s in data:
        number = s.get("number")
        if number is None:# drop the record if number is missing, as it's the primary key for station and foreign key for availability
            continue
        # station only keeps one record ( number is key)
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

        # availability keeps every record
        last_update_ms = s.get("last_update")
        last_update_dt = None
        if last_update_ms:
            # standardize to UTC datetime, as the API returns timestamp in milliseconds, for later machine learning use
            last_update_dt = datetime.fromtimestamp(last_update_ms / 1000, tz=timezone.utc)
       
        availability_rows.append({
            "number": number,
            "available_bike_stands": s.get("available_bike_stands"),
            "available_bikes": s.get("available_bikes"),
            "status": s.get("status"),
            "last_update": last_update_dt,
        })

print(f"station has {len(station_rows)} records", flush=True)
print(f"availability has {len(availability_rows)} records", flush=True)

# Batch write (upsert for station to save time and resources; direct insert for availability)
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

print("Data import completed", flush=True)
