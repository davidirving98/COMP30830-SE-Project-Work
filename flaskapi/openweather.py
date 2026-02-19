import requests
import os

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

CITY = "Dublin"

def get_weather():
    url = ( f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={CITY}&appid={OPENWEATHER_API_KEY}&units=metric" )

    response = requests.get(url)
    
    if response.status_code != 200:
        return None
    
    data = response.json()

    weather = {
        "city": data["name"],
        "temperature": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "weather": data["weather"][0]["description"],
        "wind_speed": data["wind"]["speed"] }

    return weather


