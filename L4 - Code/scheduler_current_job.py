import requests
import traceback
import datetime
import time
import os
import weatherinfo
import json
import sqlalchemy as sqla
from sqlalchemy import create_engine, text
import traceback
import glob
import os
from pprint import pprint
import requests
import time
from IPython.display import display

def weather_current_to_db(current_data, in_engine):

    # let us load only the parts that we have included in our db:
    # dt DATETIME NOT NULL,
    # main VARCHAR(256),
    # description VARCHAR(256),
    # temp FLOAT,
    # wind_speed FLOAT,
    # snapshot_time DATETIME

    # let us extract the relevant info from the dictionary
    if current_data.get("cod") != 200:
        raise ValueError(f"OpenWeather error: {current_data}")

    dt = datetime.datetime.fromtimestamp(current_data.get("dt"), tz=datetime.timezone.utc)
    main = current_data.get("weather", [{}])[0].get("main")
    description = current_data.get("weather", [{}])[0].get("description")
    temp = current_data.get("main", {}).get("temp")
    wind_speed = current_data.get("wind", {}).get("speed")
    snapshot_time = datetime.datetime.now(datetime.timezone.utc)

    curr_vals = (dt, main, description, temp, wind_speed, snapshot_time)

    # now let us use the engine to insert into table current
    sql = text("""
        INSERT INTO current (dt, main, description, temp, wind_speed, snapshot_time)
        VALUES (:dt, :main, :description, :temp, :wind_speed, :snapshot_time)
    """)

    vals = {
        "dt": dt,
        "main": main,
        "description": description,
        "temp": temp,
        "wind_speed": wind_speed,
        "snapshot_time": snapshot_time,
    }

    with in_engine.begin() as conn:
        conn.execute(sql, vals)

def main():
    USER = "root"
    PASSWORD = "Christen9812"
    PORT = "3306"
    DB = "local_database_weather"
    URI = "127.0.0.1"

    connection_string = "mysql+pymysql://{}:{}@{}:{}/{}".format(USER, PASSWORD, URI, PORT, DB)

    engine = create_engine(connection_string, echo = True)

    try:
        current_r = requests.get(weatherinfo.CURRENT_WEATHER_URI, params=
        {"lat": "53.3498006", "lon": "-6.2602964", "appid": weatherinfo.appid, "units": "metric"})
        current_data = current_r.json()
        weather_current_to_db(current_data, engine)
    except:
        print(traceback.format_exc())

# CTRL + Z or CTRL + C to stop it
main()

