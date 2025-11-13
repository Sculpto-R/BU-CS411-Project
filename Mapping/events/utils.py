# events/utils.py
import requests
from django.conf import settings

def get_coordinates(address: str):
    """
    Returns (lat, lng) for a given address using Google Geocoding API,
    or (None, None) if it can't be geocoded.
    """
    if not address:
        return None, None

    params = {
        "address": address,
        "key": settings.GOOGLE_MAPS_API_KEY,
    }
    response = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params=params,
        timeout=10,
    )
    data = response.json()

    if data.get("status") == "OK" and data.get("results"):
        location = data["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]

    # You might want to log this
    print("Geocoding error:", data.get("status"), "for", address)
    return None, None
