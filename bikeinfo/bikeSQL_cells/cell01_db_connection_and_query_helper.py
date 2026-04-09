import os
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pandas as pd
import sqlalchemy as sqla
from sqlalchemy.engine import URL

# Load project root config.py by absolute file path.
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
print("config checked", flush=True)

DB_NAME = getattr(config, "DB_NAME", "COMP30830_SW")

engine = sqla.create_engine(
    URL.create(
        drivername="mysql+pymysql",
        username=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=getattr(config, "DB_PORT", 3306),
        database=DB_NAME,
    )
)


def q(sql, params=None):
    """Run SQL and return a DataFrame."""
    return pd.read_sql(sqla.text(sql), engine, params=params)
