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

connection_string = "mysql+pymysql://{}:{}@{}:{}".format(USER, PASSWORD, URI, PORT)

engine = create_engine(connection_string, echo = True)

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
