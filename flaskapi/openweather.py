import requests
import os

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
        "weather": data["weather"][0]["main"],
        "wind_speed": data["wind"]["speed"],
        "humidity": data["main"]["humidity"]}

    return weather

