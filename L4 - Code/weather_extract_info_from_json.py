import requests
import traceback
import datetime
import time
import os
import weatherinfo
import json


def weather_current_to_db(text):
    # let us load the current weather data from the text received from OpenWeather
    current_data = json.loads(text)

    # print type of the current_data object, and number of current_data
    print(type(current_data), len(current_data))

    # let us print the type of the object current_data (a dictionary) and load the content
    for curr in current_data:
        print(type(curr))

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
    print(curr_vals)


def weather_forecast_to_db(text):
    # let us load the forecast weather data from the text received from OpenWeather
    forecast_data = json.loads(text)

    # print type of the forecast_data object, and number of forecast_data
    print(type(forecast_data), len(forecast_data))

    # let us print the type of the object forecast_data (a dictionary) and load the content
    for fore in forecast_data:
        print(type(fore))

    # let us load only the parts that we have included in our db:
    # future_dt DATETIME NOT NULL,
    # main VARCHAR(256),
    # description VARCHAR(256),
    # temp FLOAT,
    # wind_speed FLOAT,
    # snapshot_time DATETIME

    # let us extract the relevant info from the dictionary
    snapshot_time = datetime.datetime.now(datetime.timezone.utc)
    for item in forecast_data.get("list", []):
        future_dt = datetime.datetime.fromtimestamp(item["dt"], tz=datetime.timezone.utc)
        main = item.get("weather", [{}])[0].get("main")
        description = item.get("weather", [{}])[0].get("description")
        temp = item.get("main", {}).get("temp")
        wind_speed = item.get("wind", {}).get("speed")

    fore_vals = (future_dt, main, description, temp, wind_speed, snapshot_time)
    print(fore_vals)

def main():
    USER = "root"
    PASSWORD = "Christen9812"
    PORT = "3306"
    DB = "local_database_weather"
    URI = "127.0.0.1"

    connection_string = "mysql+pymysql://{}:{}@{}:{}/{}".format(USER, PASSWORD, URI, PORT, DB)

    try:
        current_r = requests.get(weatherinfo.CURRENT_WEATHER_URI, params=
        {"lat": "53.3498006", "lon": "-6.2602964", "appid": weatherinfo.appid, "units": "metric"})
        weather_current_to_db(current_r.text)

        forecast_r = requests.get(weatherinfo.FORECAST_WEATHER_URI, params=
        {"lat": "53.3498006", "lon": "-6.2602964", "appid": weatherinfo.appid, "units": "metric"})
        weather_forecast_to_db(forecast_r.text)

    except:
        print(traceback.format_exc())
        time.sleep(60)

# CTRL + Z or CTRL + C to stop it
main()
