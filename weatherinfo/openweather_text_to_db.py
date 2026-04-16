import requests
import traceback
import datetime
import time
import os
import sys
from pathlib import Path
import weatherinfo
import json
import sqlalchemy as sqla
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import traceback
import glob
import os
from pprint import pprint
import requests
import time
from IPython.display import display

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
import config

def weather_current_to_db(current_data, in_engine):

    # let us load only the parts that we have included in our db:
    # dt DATETIME NOT NULL,
    # main VARCHAR(256),
    # description VARCHAR(256),
    # temp FLOAT,
    # humidity FLOAT,
    # pressure FLOAT,
    # wind_speed FLOAT,
    # snapshot_time DATETIME

    # let us extract the relevant info from the dictionary
    if current_data.get("cod") != 200:
        raise ValueError(f"OpenWeather error: {current_data}")

    dt = datetime.datetime.fromtimestamp(current_data.get("dt"), tz=datetime.timezone.utc)
    main = current_data.get("weather", [{}])[0].get("main")
    description = current_data.get("weather", [{}])[0].get("description")
    temp = current_data.get("main", {}).get("temp")
    humidity = current_data.get("main", {}).get("humidity")
    pressure = current_data.get("main", {}).get("pressure")
    wind_speed = current_data.get("wind", {}).get("speed")
    snapshot_time = datetime.datetime.now(datetime.timezone.utc)

    curr_vals = (dt, main, description, temp, humidity, pressure, wind_speed, snapshot_time)

    # now let us use the engine to insert into table weather
    sql = text("""
        INSERT INTO curr_weather (dt, main, description, temp, humidity, pressure, wind_speed, snapshot_time)
        VALUES (:dt, :main, :description, :temp, :humidity, :pressure, :wind_speed, :snapshot_time)
    """)

    vals = {
        "dt": dt,
        "main": main,
        "description": description,
        "temp": temp,
        "humidity": humidity,
        "pressure": pressure,
        "wind_speed": wind_speed,
        "snapshot_time": snapshot_time,
    }

    with in_engine.begin() as conn:
        conn.execute(sql, vals)


def weather_forecast_to_db(forecast_data, in_engine):
    snapshot_time = datetime.datetime.now(datetime.timezone.utc)
    sql = text("""
        INSERT INTO forecast_weather (future_dt, main, description, temp, humidity, pressure, wind_speed, snapshot_time)
        VALUES (:future_dt, :main, :description, :temp, :humidity, :pressure, :wind_speed, :snapshot_time)
        """)
    # let us limit data insert to the next 24 hours
    forecast_list = forecast_data.get("list", []) [:8]

    with in_engine.begin() as conn:
        # let us load only the parts that we have included in our db:
        # future_dt DATETIME NOT NULL,
        # main VARCHAR(256),
        # description VARCHAR(256),
        # temp FLOAT,
        # humidity FLOAT,
        # pressure FLOAT,
        # wind_speed FLOAT,
        # snapshot_time DATETIME

        # let us extract the relevant info from the dictionary
        for item in forecast_list:
            future_dt = datetime.datetime.fromtimestamp(item["dt"], tz=datetime.timezone.utc)
            main = item.get("weather", [{}])[0].get("main")
            description = item.get("weather", [{}])[0].get("description")
            temp = item.get("main", {}).get("temp")
            humidity = item.get("main", {}).get("humidity")
            pressure = item.get("main", {}).get("pressure")
            wind_speed = item.get("wind", {}).get("speed")

            vals = {
                "future_dt": future_dt,
                "main": main,
                "description": description,
                "temp": temp,
                "humidity": humidity,
                "pressure": pressure,
                "wind_speed": wind_speed,
                "snapshot_time": snapshot_time,
            }

            conn.execute(sql, vals)


def main():
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

    try:
        current_r = requests.get(weatherinfo.CURRENT_WEATHER_URI, params=
        {"lat": "53.3498006", "lon": "-6.2602964", "appid": weatherinfo.appid, "units": "metric"})
        current_data = current_r.json()
        weather_current_to_db(current_data, engine)
        # time.sleep(60*60)
    except:
        print(traceback.format_exc())


    try:
        forecast_r = requests.get(weatherinfo.FORECAST_WEATHER_URI, params=
        {"lat": "53.3498006", "lon": "-6.2602964", "appid": weatherinfo.appid, "units": "metric"})
        forecast_data = forecast_r.json()
        weather_forecast_to_db(forecast_data, engine)
        # time.sleep(3*60*60)
    except:
        print(traceback.format_exc())

# CTRL + Z or CTRL + C to stop it
main()
