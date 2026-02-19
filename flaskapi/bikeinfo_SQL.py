from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sqlalchemy as sqla
import config
import sys


# load config.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
# define engine as a entrance to the database, using config.py for credentials and connection info
engine = sqla.create_engine(
    f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}"
    f"@{config.DB_HOST}:{getattr(config, 'DB_PORT', 3306)}/{config.DB_NAME}"
)


def _fetch_all(
    sql, params=None
):  # Helper function to execute SQL and return list of dicts
    with engine.connect() as conn:
        rows = conn.execute(
            sqla.text(sql), params or {}
        ).mappings()  #  Use .mappings() to get dict-like rows
        return [dict(row) for row in rows]  # Convert RowMapping to regular dict


def get_stations_sql():
    return _fetch_all("SELECT * FROM station")


def get_availability_sql():
    return _fetch_all("SELECT * FROM availability")


def get_station_sql(
    station_id,
):  # the data returned is merged by station and availability tables together.
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
