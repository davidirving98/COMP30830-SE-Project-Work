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
    ),
    echo=True,
)

sql = """
CREATE DATABASE IF NOT EXISTS {};
""".format(DB)

with engine.begin() as conn:
    conn.execute(text(sql))

with engine.connect() as conn:
    for res in conn.execute(text("SHOW VARIABLES;")):
        print(res)


"""
engine.execute(sql)

for res in engine.execute("SHOW VARIABLES;"):
    print(res)
"""
