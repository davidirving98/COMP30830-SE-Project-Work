import sys
from pathlib import Path
import sqlalchemy as sqla

# Resolve bikeinfo/config.py relative to this file.
BIKEINFO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BIKEINFO_DIR))
import config
print("config checked", flush=True)

DB_NAME = getattr(config, "DB_NAME", "postgres")

# Connect to PostgreSQL admin DB and create target DB if missing.
engine = sqla.create_engine(
    f"postgresql+psycopg2://{config.DB_USER}:{config.DB_PASSWORD}"
    f"@{config.DB_HOST}:{getattr(config, 'DB_PORT', 5432)}/postgres"
    f"?sslmode={getattr(config, 'DB_SSLMODE', 'require')}"
)

with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
    exists = conn.execute(
        sqla.text("SELECT 1 FROM pg_database WHERE datname = :name"),
        {"name": DB_NAME}
    ).fetchone() is not None

    if exists:
        print(f"Database already exists: {DB_NAME}", flush=True)
    else:
        conn.execute(sqla.text(f'CREATE DATABASE "{DB_NAME}"'))
        print(f"Database created: {DB_NAME}", flush=True)
