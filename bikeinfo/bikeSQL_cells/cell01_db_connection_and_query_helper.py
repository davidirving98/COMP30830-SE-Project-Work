import os
import sys
from pathlib import Path

import pandas as pd
import sqlalchemy as sqla

# Resolve bikeinfo/config.py relative to this file.
BIKEINFO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BIKEINFO_DIR))
import config
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
