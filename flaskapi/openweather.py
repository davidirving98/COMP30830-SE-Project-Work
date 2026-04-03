import requests
import os
from datetime import datetime

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

LAT="53.3498006"
LON="-6.2602964"

def get_weather():
    url = ( f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={LAT}&lon={LON}&appid={OPENWEATHER_API_KEY}&units=metric" )

    response = requests.get(url)
    
    if response.status_code != 200:
        return None
    
    data = response.json()

    weather = {
        "temperature": data["main"]["temp"],
        "pressure": data["main"].get("pressure"),
        "weather": data["weather"][0]["main"],
        "wind_speed": data["wind"]["speed"],
        "humidity": data["main"]["humidity"]}

    return weather


def get_forecast(full_series=False):
    url = (f"https://pro.openweathermap.org/data/2.5/forecast/hourly"
           f"?lat={LAT}&lon={LON}&appid={OPENWEATHER_API_KEY}&units=metric")

    response = requests.get(url)

    if response.status_code != 200:
        return None

    data = response.json()
    forecast_list = data["list"]
    if full_series:
        return [
            {
                "dt": item["dt"],
                "forecast_time": datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d %H:%M:%S"),
                "temperature": item["main"]["temp"],
                "pressure": item["main"].get("pressure"),
                "weather": item["weather"][0]["main"],
                "humidity": item["main"]["humidity"],
            }
            for item in forecast_list
        ]

    f1 = forecast_list[0]
    f3 = forecast_list[2]

    forecast_weather = [
        {
            "forecast_time": datetime.fromtimestamp(f1["dt"]).strftime("%H:%M"),
            "temperature": f1["main"]["temp"],
            "weather": f1["weather"][0]["main"],
            "humidity": f1["main"]["humidity"]
        },
        {
            "forecast_time": datetime.fromtimestamp(f3["dt"]).strftime("%H:%M"),
            "temperature": f3["main"]["temp"],
            "weather": f3["weather"][0]["main"],
            "humidity": f3["main"]["humidity"]
        }
    ]
    return forecast_weather
