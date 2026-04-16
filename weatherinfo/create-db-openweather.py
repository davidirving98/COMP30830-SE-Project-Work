import weatherinfo
import requests
import json
import sqlalchemy as sqla
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.engine import URL
import traceback
import glob
import os
import sys
from pathlib import Path
from pprint import pprint
import simplejson as json
import time
from IPython.display import display

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
import config

USER = config.DB_USER
PASSWORD = config.DB_PASSWORD
PORT = str(config.DB_PORT)
DB = config.DB_NAME
URI = config.DB_HOST

engine = create_engine(
    URL.create(
        "mysql+pymysql",
        username=USER,
        password=PASSWORD,
        host=URI,
        port=int(PORT),
        database=DB,
    ),
    echo=True,
)


# Let us create a simplified current table: ADD ALL YOUR VARIABLES!
# VARCHAR(256) indicates a string with max 256 chars

sql = '''
CREATE TABLE IF NOT EXISTS curr_weather (
dt DATETIME NOT NULL,
main VARCHAR(256),
description VARCHAR(256),
temp FLOAT,
humidity FLOAT,
pressure FLOAT,
wind_speed FLOAT,
snapshot_time DATETIME,
PRIMARY KEY (dt)
);
'''

with engine.begin() as conn:
    conn.execute(text(sql))

# Fetch and print the result to see the columns of the table
with engine.connect() as conn:
    tab_structure = conn.execute(text("SHOW COLUMNS FROM curr_weather;"))
    columns = tab_structure.fetchall()
    print(columns)

##################CREATE forecast(hourly) TABLE: DO NOT FORGET ALL VARIABLES############
sql = """
CREATE TABLE IF NOT EXISTS forecast_weather (
future_dt DATETIME NOT NULL,
main VARCHAR(256),
description VARCHAR(256),
temp FLOAT,
humidity FLOAT,
pressure FLOAT,
wind_speed FLOAT,
snapshot_time DATETIME,
PRIMARY KEY (future_dt, snapshot_time)
);
"""

with engine.begin() as conn:
    conn.execute(text(sql))

# Ensure new columns exist even if tables were already created earlier.
with engine.begin() as conn:
    conn.execute(text("ALTER TABLE curr_weather ADD COLUMN IF NOT EXISTS humidity FLOAT"))
    conn.execute(text("ALTER TABLE curr_weather ADD COLUMN IF NOT EXISTS pressure FLOAT"))
    conn.execute(text("ALTER TABLE forecast_weather ADD COLUMN IF NOT EXISTS humidity FLOAT"))
    conn.execute(text("ALTER TABLE forecast_weather ADD COLUMN IF NOT EXISTS pressure FLOAT"))
