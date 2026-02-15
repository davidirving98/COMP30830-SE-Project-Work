####################DOWNLOAD from OPEN WEATHER###############
import requests
import traceback
import datetime
import time
import os
import weatherinfo

"""
Data are in weatherinfo.py
    appid = "d591528884f1259a6b39b08083ceaa5e"
    CURRENT_WEATHER_URI = "https://api.openweathermap.org/data/2.5/weather"
    FORECAST_WEATHER_URI = "https://api.openweathermap.org/data/2.5/forecast"
    dublin_lat = 53.3498006
    dublin_lon = -6.2602964
"""

# Will be used to store text in a file
def write_to_file(text, tag):
    # I first need to create a folder data where the files will be stored.
    
    if not os.path.exists('weather_data'):
        os.mkdir('weather_data')
        print("Folder 'weather_data' created!")
    else:
        print("Folder 'weather_data' already exists.")

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"weather_data/{tag}_{ts}.json"

    # now is a variable from datetime, which will go in {}.
    # replace is replacing white spaces with underscores in the file names
    with open(filename, "w") as f:
        f.write(text)

# Empty for now
def write_to_db(text):
    return 0

def main():
    while True:
        try:
            current_r = requests.get(weatherinfo.CURRENT_WEATHER_URI, params=
            {"lat": weatherinfo.dublin_lat, "lon": weatherinfo.dublin_lon, "appid": weatherinfo.appid, "units": "metric"})
            print(current_r)
            write_to_file(current_r.text, "current")

            forecast_r = requests.get(weatherinfo.FORECAST_WEATHER_URI, params=
            {"lat": weatherinfo.dublin_lat, "lon": weatherinfo.dublin_lon, "appid": weatherinfo.appid, "units": "metric"})
            print(forecast_r)
            write_to_file(forecast_r.text, "forecast")

            time.sleep(60*60)
        except:
            print(traceback.format_exc())

# CTRL + Z to stop it
main()

