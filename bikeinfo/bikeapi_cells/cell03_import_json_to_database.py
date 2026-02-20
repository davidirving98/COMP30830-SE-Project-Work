import json
from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import sqlalchemy as sqla

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config.py"
spec = spec_from_file_location("project_config", CONFIG_PATH)
config = module_from_spec(spec)
spec.loader.exec_module(config)

engine = sqla.create_engine(
    f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}"
    f"@{config.DB_HOST}:{getattr(config, 'DB_PORT', 3306)}/{getattr(config, 'DB_NAME', 'COMP30830_SW')}"
)

with engine.begin() as conn:
    conn.execute(sqla.text("""
        CREATE TABLE IF NOT EXISTS station (
            number INT PRIMARY KEY,
            contract_name VARCHAR(64), name VARCHAR(128), address VARCHAR(256),
            lat DECIMAL(9,6), lng DECIMAL(9,6), banking BOOLEAN, bonus BOOLEAN, bike_stands INT
        )
    """))
    conn.execute(sqla.text("""
        CREATE TABLE IF NOT EXISTS availability (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            number INT NOT NULL,
            available_bike_stands INT, available_bikes INT, status VARCHAR(16), last_update DATETIME,
            CONSTRAINT fk_station_number FOREIGN KEY (number) REFERENCES station(number) ON DELETE CASCADE
        )
    """))
    has_index = conn.execute(
        sqla.text("SHOW INDEX FROM availability WHERE Key_name = 'idx_number_time'")
    ).first()
    if not has_index:
        conn.execute(
            sqla.text("CREATE INDEX idx_number_time ON availability (number, last_update)")
        )

input_path = Path(config.FOLDER_PATH)
json_files = (
    sorted(input_path.glob("station_status_*.json")) if input_path.is_dir() else [input_path]
)

station_rows = {}
availability_rows = []
for fp in json_files:
    for s in json.loads(fp.read_text(encoding="utf-8")):
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
        last_update = s.get("last_update")
        availability_rows.append({
            "number": number,
            "available_bike_stands": s.get("available_bike_stands"),
            "available_bikes": s.get("available_bikes"),
            "status": s.get("status"),
            "last_update": (
                datetime.fromtimestamp(last_update / 1000, tz=timezone.utc) if last_update else None
            ),
        })

station_insert = sqla.text("""
    INSERT INTO station (number, contract_name, name, address, lat, lng, banking, bonus, bike_stands)
    VALUES (:number, :contract_name, :name, :address, :lat, :lng, :banking, :bonus, :bike_stands)
    ON DUPLICATE KEY UPDATE
        contract_name = VALUES(contract_name), name = VALUES(name), address = VALUES(address),
        lat = VALUES(lat), lng = VALUES(lng), banking = VALUES(banking),
        bonus = VALUES(bonus), bike_stands = VALUES(bike_stands)
""")
availability_insert = sqla.text("""
    INSERT INTO availability (number, available_bike_stands, available_bikes, status, last_update)
    VALUES (:number, :available_bike_stands, :available_bikes, :status, :last_update)
""")

with engine.begin() as conn:
    if station_rows:
        conn.execute(station_insert, list(station_rows.values()))
    if availability_rows:
        conn.execute(availability_insert, availability_rows)

print(f"Imported station={len(station_rows)}, availability={len(availability_rows)}")
