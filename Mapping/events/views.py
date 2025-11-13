# events/views.py
from pathlib import Path
import csv

from django.conf import settings
from django.shortcuts import render

from .utils import get_coordinates  # keep for fallback, or remove if not needed


def index(request):
    events = []

    # Adjust if your CSV is in a different folder
    csv_path = Path(settings.BASE_DIR) / "data_scripts" / "event_scraping" / "events_out.csv"

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Core fields from your header
            name = row.get("event_title") or "Untitled event"
            address = row.get("address") or ""
            date = row.get("start_local") or ""
            city = row.get("city") or ""

            # Try to use latitude/longitude from CSV first
            lat = row.get("latitude")
            lng = row.get("longitude")

            try:
                lat = float(lat) if lat not in (None, "", "NaN") else None
                lng = float(lng) if lng not in (None, "", "NaN") else None
            except ValueError:
                lat, lng = None, None

            # Optional: only show London events
            # if city and city.lower() != "london":
            #     continue

            # Fallback: geocode if coords are missing but we have an address
            if (lat is None or lng is None) and address:
                lat, lng = get_coordinates(address)

            # If we still don't have coords, skip this event (can't map it)
            if lat is None or lng is None:
                continue

            events.append(
                {
                    "name": name,
                    "address": address or f"{row.get('venue_name', '')}, {city}",
                    "date": date,
                    "lat": lat,
                    "lng": lng,
                }
            )

    return render(request, "events/map.html", {"events": events})
