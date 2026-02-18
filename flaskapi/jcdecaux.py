import requests

JCDECAUX_API_KEY = "d0241f321be26bec04b72f41626ca43cb4ec482e"

CONTRACT = "dublin"

def get_stations():
    url = ( "https://api.jcdecaux.com/vls/v1/stations"f"?contract={CONTRACT}&apiKey={JCDECAUX_API_KEY}" )

    response = requests.get(url)

    if response.status_code != 200:
        return None

    data = response.json()

    stations = []

    for station in data:
        stations.append({
            "number": station["number"],
            "name": station["name"],
            "available_bikes": station["available_bikes"],
            "available_stands": station["available_bike_stands"],
            "lat": station["position"]["lat"],
            "lng": station["position"]["lng"] })

    return stations

def get_station(station_id):

    url = ( "https://api.jcdecaux.com/vls/v1/stations"f"?contract={CONTRACT}&apiKey={JCDECAUX_API_KEY}" )

    response = requests.get(url)

    if response.status_code != 200:
        return None
    
    data = response.json()

    for station in data:
        if station["number"] == station_id:
            return {
            "number": station["number"],
            "name": station["name"],
            "available_bikes": station["available_bikes"],
            "available_stands": station["available_bike_stands"],
            "lat": station["position"]["lat"],
            "lng": station["position"]["lng"] }

    return None
                
