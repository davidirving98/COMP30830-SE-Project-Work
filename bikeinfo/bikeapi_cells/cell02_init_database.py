from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sqlalchemy as sqla

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

# Connect to MySQL server and create target DB if missing.
engine = sqla.create_engine(
    f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}"
    f"@{config.DB_HOST}:{getattr(config, 'DB_PORT', 3306)}/"
)

with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
    conn.execute(
        sqla.text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4")
    )
    print(f"Database ready: {DB_NAME}", flush=True)
