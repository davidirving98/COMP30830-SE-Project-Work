import requests
import os

JCDECAUX_API_KEY = os.getenv("JCDECAUX_API_KEY")
CONTRACT = "dublin"

def get_stations():
    """
    Fetch all station snapshots from JCDecaux API.

    :returns: Station list with selected fields, or ``None`` on API failure.
    :rtype: list[dict] | None
    """
    url = (
        "https://api.jcdecaux.com/vls/v1/stations"
        f"?contract={CONTRACT}&apiKey={JCDECAUX_API_KEY}"
    )

    response = requests.get(url)

    if response.status_code != 200:
        return None
    data = response.json()
    stations = []
    for station in data:
        stations.append(
            {
                "number": station["number"],
                "name": station["name"],
                "available_bikes": station["available_bikes"],
                "available_stands": station["available_bike_stands"],
                "lat": station["position"]["lat"],
                "lng": station["position"]["lng"],
            }
        )
    return stations


def get_station(station_id):
    """
    Fetch one station snapshot by station id.

    :param station_id: Station numeric identifier.
    :type station_id: int
    :returns: Station payload, or ``None`` if not found/API failure.
    :rtype: dict | None
    """

    url = (
        "https://api.jcdecaux.com/vls/v1/stations"
        f"?contract={CONTRACT}&apiKey={JCDECAUX_API_KEY}"
    )
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
                "lng": station["position"]["lng"],
            }

    return None


def fetch_stations_raw():
    """
    Fetch raw station payload from JCDecaux API.

    :returns: Raw API JSON list, or ``None`` on API failure.
    :rtype: list[dict] | None
    """
    url = (
        "https://api.jcdecaux.com/vls/v1/stations"
        f"?contract={CONTRACT}&apiKey={JCDECAUX_API_KEY}"
    )

    response = requests.get(url)

    if response.status_code != 200:
        return None

    return response.json()
