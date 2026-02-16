import json
import time
from datetime import datetime, timezone, timedelta
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import requests

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
_spec.loader.exec_module(config)  # api info should not be shown in public

output_dir = Path("data/dublinbike_status")
output_dir.mkdir(parents=True, exist_ok=True)

def fetch_and_save_once():
    ts = datetime.now(timezone.utc)
    ts_str = ts.strftime("%Y%m%dT%H%M%SZ")
    filename = output_dir / f"station_status_{ts_str}.json"
    try:
        print(f"[{ts.strftime('%Y-%m-%d %H:%M:%S')} UTC] Fetching from JCD API", flush=True)
        resp = requests.get(config.BIKE_STATUS_URL, timeout=20) # set timeout 
        print(f"[{ts.strftime('%Y-%m-%d %H:%M:%S')} UTC] Status Code: {resp.status_code}", flush=True)
        resp.raise_for_status() # raise exception for HTTP errors
        data = resp.json() # may raise JSONDecodeError if response is not valid JSON
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False) # save info in UTF-8 format
        print(f"[{ts.strftime('%Y-%m-%d %H:%M:%S')} UTC] Saved: {filename}", flush=True)
        print(f"[{ts.strftime('%Y-%m-%d %H:%M:%S')} UTC] Next update in 5 minutes...", flush=True)
    except Exception as e:
        print(f"[{ts.strftime('%Y-%m-%d %H:%M:%S')} UTC] Error: {e}; will retry next cycle", flush=True)


max_hours = 48 
end_time = datetime.now(timezone.utc) + timedelta(hours=max_hours) #keep fetching for 48 hours, then stop,or manually stop by clicking button in jupyter notebook

while datetime.now(timezone.utc) < end_time:
    fetch_and_save_once()
    time.sleep(300) #sleep for 5 minutes
print("done: reached 48h timeout")
