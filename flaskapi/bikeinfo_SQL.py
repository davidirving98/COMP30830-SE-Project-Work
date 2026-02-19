from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sqlalchemy as sqla


# load config.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config.py"
if not CONFIG_PATH.exists():
    raise FileNotFoundError(f"Missing config file: {CONFIG_PATH}")

_spec = spec_from_file_location("project_config", CONFIG_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load config from: {CONFIG_PATH}")
config = module_from_spec(_spec)
_spec.loader.exec_module(config)


engine = sqla.create_engine(
    f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}"
    f"@{config.DB_HOST}:{getattr(config, 'DB_PORT', 3306)}/{config.DB_NAME}"
)


def _fetch_all(sql, params=None):
    with engine.connect() as conn:
        rows = conn.execute(sqla.text(sql), params or {}).mappings()
        return [dict(row) for row in rows]


def get_stations_sql():
    return _fetch_all("SELECT * FROM station")


def get_availability_sql():
    return _fetch_all("SELECT * FROM availability")


def get_station_sql(station_id):
    sql = """
    SELECT
        s.number,
        s.name,
        a.available_bikes,
        a.available_bike_stands AS available_stands,
        s.lat,
        s.lng
    FROM station s
    JOIN (
        SELECT number, MAX(last_update) AS max_last_update
        FROM availability
        GROUP BY number
    ) latest
        ON latest.number = s.number
    JOIN availability a
        ON a.number = latest.number
       AND a.last_update = latest.max_last_update
    WHERE s.number = :station_id
    """
    rows = _fetch_all(sql, {"station_id": station_id})
    return rows[0] if rows else None


def search_stations_sql(filters):
    sql = """
    SELECT
        s.number,
        s.name,
        a.available_bikes,
        a.available_bike_stands AS available_stands,
        s.lat,
        s.lng
    FROM station s
    JOIN (
        SELECT number, MAX(last_update) AS max_last_update
        FROM availability
        GROUP BY number
    ) latest
        ON latest.number = s.number
    JOIN availability a
        ON a.number = latest.number
       AND a.last_update = latest.max_last_update
    """

    where = []
    params = {}

    if filters.get("number") is not None:
        where.append("s.number = :number")
        params["number"] = filters["number"]
    if filters.get("name"):
        where.append("s.name LIKE :name")
        params["name"] = f"%{filters['name']}%"
    if filters.get("available_bikes") is not None:
        where.append("a.available_bikes = :available_bikes")
        params["available_bikes"] = filters["available_bikes"]
    if filters.get("available_stands") is not None:
        where.append("a.available_bike_stands = :available_stands")
        params["available_stands"] = filters["available_stands"]
    if filters.get("lat") is not None:
        where.append("s.lat = :lat")
        params["lat"] = filters["lat"]
    if filters.get("lng") is not None:
        where.append("s.lng = :lng")
        params["lng"] = filters["lng"]

    if where:
        sql += " WHERE " + " AND ".join(where)

    sql += " ORDER BY s.number"
    return _fetch_all(sql, params)
