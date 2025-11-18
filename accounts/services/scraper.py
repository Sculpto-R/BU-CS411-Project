"""
scraper.py
This module fetches events based on user preferences
and converts them to a consistent event JSON structure.
"""

import requests
import logging

logger = logging.getLogger("accounts.scraper")

API_URL = "http://127.0.0.1:8000/api/events/"

def fetch_events_for_preferences(profile, center=None, radius_m=5000):
    """
    Fetch events that match the user's preferences by calling the API layer.
    
    Args:
        profile: User profile
        center: (lat, lon) tuple OR None defaults to London
        radius_m: radius in meters
    """
    if profile is None:
        return []

    # Default location: central London
    if center is None:
        center = (51.5074, -0.1278)

    # Normalize preference structure
    def norm_list(x):
        if x is None:
            return []
        if isinstance(x, list):
            return x
        if isinstance(x, str):
            return [i.strip() for i in x.split(',') if i.strip()]
        return [str(x)]

    interests = norm_list(profile.presets) + norm_list(profile.custom_preferences)

    try:
        params = {
            "lat": center[0],
            "lon": center[1],
            "radius": radius_m,
            "preferences": ",".join(interests),
        }
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        return data.get("events", [])

    except Exception as e:
        logger.error("Failed to fetch events for preferences: %s", e)
        return []
