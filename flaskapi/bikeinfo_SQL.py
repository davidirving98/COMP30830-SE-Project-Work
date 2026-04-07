import sqlalchemy as sqla
import sys
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config


# config  provides database connection info and api keys, and also defines paths for local data storage (if needed)
def _build_connection_string():
    return sqla.engine.URL.create(
        drivername="mysql+pymysql",
        username=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
    )


# define engine as a entrance to the database, using config.py for credentials and connection info
engine = sqla.create_engine(_build_connection_string())


# Helper function to execute SQL and return list of dicts
def _fetch_all(sql, params=None):
    with engine.connect() as conn:
        rows = conn.execute(
            sqla.text(sql), params or {}
        ).mappings()  #  Use .mappings() to get dict-like rows
        return [dict(row) for row in rows]  # Convert RowMapping to regular dict


# main function to fetch data from database, used in app.py to serve API endpoints
def get_stations_sql():
    return _fetch_all("SELECT * FROM station")


# fetch availability data from database
def get_availability_sql():
    return _fetch_all("SELECT * FROM availability")


# the data returned is merged by station and availability tables together.
def get_station_sql(
    station_id,
):
    sql = """
    SELECT
        s.number,
        s.name,
        a.available_bikes,
        a.available_bike_stands AS available_stands,
        s.lat,
        s.lng
    FROM station s
    JOIN availability a
        ON a.number = s.number
    WHERE s.number = :station_id
    ORDER BY a.last_update DESC
    LIMIT 1
    """
    rows = _fetch_all(sql, {"station_id": station_id})
    return rows[0] if rows else None


# get timeseries data from availability table.
def get_station_history_sql(station_id):
    sql = """
    SELECT
        DATE_FORMAT(t.last_update, '%Y-%m-%d %H:%i:%s') AS last_update,
        t.available_bikes,
        t.available_bike_stands
    FROM (
        SELECT
            a.last_update,
            a.available_bikes,
            a.available_bike_stands
        FROM availability a
        WHERE a.number = :station_id
        ORDER BY a.last_update DESC, a.id DESC
        LIMIT 5
    ) t
    ORDER BY t.last_update ASC
    """
    return _fetch_all(sql, {"station_id": station_id})


def get_prediction_db_features(station_id, target_time):
    """
    Build DB-derived model features for one station at target_time:
    - number, capacity(bike_stands), lat, lng
    - bikes_1d_mean, bikes_same_slot_mean from availability history prior to target_time
    """
    sql = """
    SELECT
        s.number AS number,
        s.bike_stands AS capacity,
        s.lat AS lat,
        s.lng AS lng,
        (
            SELECT AVG(a1.available_bikes)
            FROM availability a1
            WHERE a1.number = s.number
              AND a1.last_update < :target_time
              AND a1.last_update >= DATE_SUB(:target_time, INTERVAL 1 DAY)
        ) AS bikes_1d_mean,
        (
            SELECT AVG(aslot.available_bikes)
            FROM availability aslot
            WHERE aslot.number = s.number
              AND aslot.last_update < :target_time
              AND HOUR(aslot.last_update) = HOUR(:target_time)
        ) AS bikes_same_slot_mean
    FROM station s
    WHERE s.number = :station_id
    LIMIT 1
    """
    rows = _fetch_all(sql, {"station_id": station_id, "target_time": target_time})
    return rows[0] if rows else None


# get latest view data from database, which is updated every time the front page loads and fetches new data from API
def get_latest_stations_view():
    sql = """
    SELECT
        s.number,
        s.name,
        a.available_bikes,
        a.available_bike_stands AS available_stands,
        s.lat,
        s.lng
    FROM station s
    JOIN availability a
        ON a.number = s.number
    WHERE a.id = (
        SELECT a2.id
        FROM availability a2
        WHERE a2.number = s.number
        ORDER BY a2.last_update DESC, a2.id DESC
        LIMIT 1
    )
    """
    return _fetch_all(sql)


# get the latest refresh time from the availability table
def get_latest_refresh_time():
    sql = "SELECT MAX(last_update) AS last_update FROM availability"
    rows = _fetch_all(sql)
    return rows[0]["last_update"] if rows else None


# function to save raw data from API to database, called in app.py when front page loads and fetches new data from API
# share the same strategy with incell04_import_api_to_database.py
def save_snapshot(raw_data):
    if not raw_data:
        return {"stations_written": 0, "availability_written": 0}
    if not isinstance(raw_data, list):
        raise ValueError("raw_data must be a list")

    station_rows = {}
    availability_rows = []

    for s in raw_data:
        number = s.get("number")
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
            last_update_dt = datetime.fromtimestamp(
                last_update_ms / 1000, tz=timezone.utc
            ).replace(tzinfo=None)

        availability_rows.append(
            {
                "number": number,
                "available_bike_stands": s.get("available_bike_stands"),
                "available_bikes": s.get("available_bikes"),
                "status": s.get("status"),
                "last_update": last_update_dt,
            }
        )

    station_insert = sqla.text(
        """
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
        bike_stands = VALUES(bike_stands)
    """
    )

    availability_insert = sqla.text(
        """
    INSERT INTO availability (number, available_bike_stands, available_bikes, status, last_update)
    VALUES (:number, :available_bike_stands, :available_bikes, :status, :last_update)
    ON DUPLICATE KEY UPDATE
        available_bike_stands = VALUES(available_bike_stands),
        available_bikes = VALUES(available_bikes),
        status = VALUES(status)
    """
    )

    with engine.begin() as conn:
        if station_rows:
            conn.execute(station_insert, list(station_rows.values()))
        if availability_rows:
            conn.execute(availability_insert, availability_rows)

    return {
        "stations_written": len(station_rows),
        "availability_written": len(availability_rows),
    }
