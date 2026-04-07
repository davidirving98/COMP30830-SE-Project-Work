import requests
from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
import sqlalchemy as sqla
from pathlib import Path
import time
from statistics import fmean

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
    sqla.engine.URL.create(
        drivername="mysql+pymysql",
        username=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=getattr(config, "DB_PORT", 3306),
        database=DB_NAME,
    )
)

INTERVALS_PER_DAY = 144
INTERVALS_PER_WEEK = 1008
MIN_PERIODS_1D = INTERVALS_PER_DAY // 2
MIN_PERIODS_SAME_SLOT = 3

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
INSERT INTO availability (
    number, available_bike_stands, available_bikes, status, last_update,
    bikes_1d_mean, bikes_same_slot_mean
)
VALUES (
    :number, :available_bike_stands, :available_bikes, :status, :last_update,
    :bikes_1d_mean, :bikes_same_slot_mean
)
ON DUPLICATE KEY UPDATE
    available_bike_stands = VALUES(available_bike_stands),
    available_bikes = VALUES(available_bikes),
    status = VALUES(status),
    bikes_1d_mean = VALUES(bikes_1d_mean),
    bikes_same_slot_mean = VALUES(bikes_same_slot_mean);
""")

history_query_template = """
SELECT available_bikes, last_update
FROM availability
WHERE number = :number AND available_bikes IS NOT NULL
ORDER BY last_update DESC, id DESC
LIMIT {limit}
"""

column_exists_sql = sqla.text("""
SELECT 1
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = :db_name
  AND TABLE_NAME = 'availability'
  AND COLUMN_NAME = :column_name
LIMIT 1
""")


def ensure_availability_feature_columns():
    with engine.begin() as conn:
        for col_name in ("bikes_1d_mean", "bikes_same_slot_mean"):
            exists = conn.execute(
                column_exists_sql,
                {"db_name": DB_NAME, "column_name": col_name},
            ).fetchone()
            if exists:
                continue
            conn.execute(
                sqla.text(
                    f"ALTER TABLE availability ADD COLUMN {col_name} DOUBLE NULL"
                )
            )
            print(f"Added column availability.{col_name}", flush=True)


def rolling_mean_with_min_periods(values, window_size, min_periods):
    usable = values[:window_size]
    if len(usable) < min_periods:
        return None
    return float(fmean(usable))


def mean_with_min_periods(values, min_periods):
    if len(values) < min_periods:
        return None
    return float(fmean(values))


def get_station_history_means(conn, station_number, target_time):
    history_rows = conn.execute(
        sqla.text(history_query_template.format(limit=INTERVALS_PER_WEEK)),
        {"number": station_number},
    ).fetchall()
    history_values = [row[0] for row in history_rows if row[0] is not None]

    bikes_1d_mean = rolling_mean_with_min_periods(
        history_values, INTERVALS_PER_DAY, MIN_PERIODS_1D
    )
    target_hour = target_time.hour if target_time is not None else None
    same_hour_values = [
        row[0]
        for row in history_rows
        if row[0] is not None
        and row[1] is not None
        and (target_hour is None or row[1].hour == target_hour)
    ]
    bikes_same_slot_mean = mean_with_min_periods(
        same_hour_values, MIN_PERIODS_SAME_SLOT
    )
    return bikes_1d_mean, bikes_same_slot_mean


def import_once():
    # Execute one pull + insert
    resp = requests.get(config.BIKE_STATUS_URL, timeout=20)
    resp.raise_for_status()
    data = resp.json()  # Here we assume the top level is a list

    station_rows = {}
    availability_rows = []

    for s in data:
        number = s.get("number")  # primary key for station and foreign key for availability
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
            "bikes_1d_mean": None,
            "bikes_same_slot_mean": None,
        })

    with engine.begin() as conn:
        for row in availability_rows:
            bikes_1d_mean, bikes_same_slot_mean = get_station_history_means(
                conn, row["number"], row["last_update"]
            )
            row["bikes_1d_mean"] = bikes_1d_mean
            row["bikes_same_slot_mean"] = bikes_same_slot_mean

        conn.execute(station_insert, list(station_rows.values()))
        conn.execute(availability_insert, availability_rows)

    print(
        f"API import completed: stations={len(station_rows)}, availability={len(availability_rows)}",
        flush=True,
    )


INTERVAL_SECONDS = 300  # 5 minutes
ensure_availability_feature_columns()
print("Start importer: run every 5 minutes. Press Ctrl+C to stop.", flush=True)
while True:
    started_at = datetime.now(timezone.utc)
    print(f"[{started_at.strftime('%Y-%m-%d %H:%M:%S')} UTC] Import started", flush=True)
    try:
        import_once()
    except Exception as e:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC] Import failed: {e}", flush=True)
    time.sleep(INTERVAL_SECONDS)
