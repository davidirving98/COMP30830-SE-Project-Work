import os
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pandas as pd
import sqlalchemy as sqla

# Load bikeinfo/config.py by absolute file path.
BIKEINFO_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BIKEINFO_DIR / "config.py"
if not CONFIG_PATH.exists():
    raise FileNotFoundError(f"Missing config file: {CONFIG_PATH}")
print(f"Using config file: {CONFIG_PATH}", flush=True)
_spec = spec_from_file_location("bikeinfo_config", CONFIG_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load config from: {CONFIG_PATH}")
config = module_from_spec(_spec)
_spec.loader.exec_module(config)
print("config checked", flush=True)

DB_NAME = getattr(config, "DB_NAME", "postgres")

engine = sqla.create_engine(
    f"postgresql+psycopg2://{config.DB_USER}:{config.DB_PASSWORD}"
    f"@{config.DB_HOST}:{getattr(config, 'DB_PORT', 5432)}/{DB_NAME}"
    f"?sslmode={getattr(config, 'DB_SSLMODE', 'require')}"
)


def q(sql, params=None):
    """Run SQL and return a DataFrame."""
    return pd.read_sql(sqla.text(sql), engine, params=params)
