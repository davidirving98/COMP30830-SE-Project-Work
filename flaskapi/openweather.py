import requests
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

LAT="53.3498006"
LON="-6.2602964"
APP_LOCAL_TZ = ZoneInfo("Europe/Dublin")


def _format_local_time_from_utc_ts(ts_seconds, fmt):
    """
    Convert a UTC timestamp to local Dublin time.

    :param ts_seconds: Unix timestamp (in seconds)
    :param fmt: Output time format string
    :return: Formatted local time string
    """
    return (
        datetime.fromtimestamp(int(ts_seconds), tz=timezone.utc)
        .astimezone(APP_LOCAL_TZ)
        .strftime(fmt)
    )

def get_weather():
    """
    Retrieve current weather data for Dublin from OpenWeather API.

    :return: Dictionary containing temperature, pressure, weather condition,
         wind speed, and humidity. Returns None if the API request fails.
    """
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
    """
    Retrieve the next 1 hour and 3 hours weather forecast data for Dublin.

    :param full_series: Whether to return full forecast data
    :return: List of forecast dictionaries, or None if request fails
    """
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
                "forecast_time": _format_local_time_from_utc_ts(
                    item["dt"], "%Y-%m-%d %H:%M:%S"
                ),
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
            "forecast_time": _format_local_time_from_utc_ts(f1["dt"], "%H:%M"),
            "temperature": f1["main"]["temp"],
            "weather": f1["weather"][0]["main"],
            "humidity": f1["main"]["humidity"]
        },
        {
            "forecast_time": _format_local_time_from_utc_ts(f3["dt"], "%H:%M"),
            "temperature": f3["main"]["temp"],
            "weather": f3["weather"][0]["main"],
            "humidity": f3["main"]["humidity"]
        }
    ]
    return forecast_weather
