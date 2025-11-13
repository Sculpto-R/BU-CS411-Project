# events/utils.py (root-level app)
import requests
from django.conf import settings


def get_coordinates(address: str):
    """
    Returns (lat, lng) for a given address using Google Geocoding API,
    or (None, None) if it can't be geocoded.
    """
    if not address:
        return None, None

    api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", None)
    if not api_key:
        # No key configured, just bail gracefully
        return None, None

    params = {
        "address": address,
        "key": api_key,
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

    # Could log this
    print("Geocoding error:", data.get("status"), "for", address)
    return None, None
