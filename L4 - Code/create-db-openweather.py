import weatherinfo
import requests
import json
import sqlalchemy as sqla
from sqlalchemy import create_engine
from sqlalchemy import text
import traceback
import glob
import os
from pprint import pprint
import simplejson as json
import time
from IPython.display import display

USER = "root"
PASSWORD = "Christen9812"
PORT = "3306"
DB = "local_database_weather"
URI = "127.0.0.1"

connection_string = "mysql+pymysql://{}:{}@{}:{}/{}".format(USER, PASSWORD, URI, PORT, DB)

engine = create_engine(connection_string, echo = True)


# Let us create a simplified current table: ADD ALL YOUR VARIABLES!
# VARCHAR(256) indicates a string with max 256 chars

sql = '''
CREATE TABLE IF NOT EXISTS current (
dt DATETIME NOT NULL,
main VARCHAR(256),
description VARCHAR(256),
temp FLOAT,
wind_speed FLOAT,
snapshot_time DATETIME,
PRIMARY KEY (dt)
);
'''

with engine.begin() as conn:
    conn.execute(text(sql))

# Fetch and print the result to see the columns of the table
with engine.connect() as conn:
    tab_structure = conn.execute(text("SHOW COLUMNS FROM current;"))
    columns = tab_structure.fetchall()
    print(columns)

##################CREATE forecast(hourly) TABLE: DO NOT FORGET ALL VARIABLES############
sql = """
CREATE TABLE IF NOT EXISTS hourly (
future_dt DATETIME NOT NULL,
main VARCHAR(256),
description VARCHAR(256),
temp FLOAT,
wind_speed FLOAT,
snapshot_time DATETIME,
PRIMARY KEY (future_dt, snapshot_time)
);
"""

with engine.begin() as conn:
    conn.execute(text(sql))


