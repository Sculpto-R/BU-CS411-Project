# accounts/services/scraper.py
"""
Scraper / mapping integration service.

Public interface:
    fetch_events_for_preferences(user_or_profile, center=(lat,lon), radius_m=5000) -> list of events

Event schema (dict):
    {
       "title": str,
       "lat": float,
       "lon": float,
       "venue_name": str|None,
       "type": str,
       "snippet": str,
       "url": str|None,
       "date": "YYYY-MM-DD" | None,
       "source": str
    }
"""

from typing import List, Dict, Tuple
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date

logger = logging.getLogger("accounts.scraper")

# Keep third-party calls isolated so unit tests can mock requests easily.
DEFAULT_CENTER = (51.5074, -0.1278)  # London

def fetch_events_for_preferences(profile, center: Tuple[float, float]=DEFAULT_CENTER, radius_m: int=5000, max_results: int=60) -> List[Dict]:
    """
    High-level function that:
      - extracts normalized preference tokens from profile
      - queries Overpass (or other venue API) for candidate venues
      - scrapes event aggregator(s) for event posts
      - attempts to match events to venues
      - returns a list of events (see schema above)

    This implementation is minimal/placeholder and intended to be expanded.
    """
    if profile is None:
        return []

    lat, lon = center
    tokens = profile.export_preferences()  # expects list of lowercase tokens
    logger.debug("Fetching events for %s tokens near %s/%s radius=%s", tokens, lat, lon, radius_m)

    # Placeholder plan:
    # 1) Query Overpass for nearby venues (or a lightweight OSM query).
    # 2) Scrape a public aggregator (like allevents.in) for London and parse available events.
    # 3) Try to match them (name substring / nearest).
    # For now we return an empty list or pseudo-suggestions.

    events = []
    # Minimal pseudo-event for placeholder
    events.append({
        "title": "Example placeholder event",
        "lat": lat + 0.001,
        "lon": lon + 0.001,
        "venue_name": "Placeholder Venue",
        "type": tokens[0] if tokens else "event",
        "snippet": "This is placeholder data until scraper is implemented.",
        "url": None,
        "date": date.today().isoformat(),
        "source": "placeholder"
    })
    return events


# Helper: a small function that scrapes a page and produces candidate events
def scrape_allevents_london(limit: int=40) -> List[Dict]:
    """
    Example helper showing how to scrape a page with BeautifulSoup.
    Keep the function small and resilient: do not throw on parse failure.
    """
    url = "https://allevents.in/london"
    try:
        r = requests.get(url, timeout=10, headers={'User-Agent': 'iNNiT-bot/0.1 (+https://innit.local)'})
        r.raise_for_status()
    except Exception as e:
        logger.warning("allevents.in fetch failed: %s", e)
        return []

    out = []
    try:
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".event-item, .event-card, .col-event-card") or soup.select(".card") or []
        for card in cards[:limit]:
            title_tag = card.select_one("h3, .card-title, .event-title, a")
            link_tag = card.select_one("a[href]")
            date_tag = card.select_one(".date, time, .event-time")
            snippet_tag = card.select_one(".description, .card-text, .event-desc")
            title = title_tag.get_text(strip=True) if title_tag else None
            url = link_tag['href'] if link_tag and link_tag.get('href') else None
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ''
            date_iso = None
            # attempt simple ISO date detection
            if date_tag:
                txt = date_tag.get_text(" ", strip=True)
                try:
                    parsed = datetime.fromisoformat(txt.strip())
                    date_iso = parsed.date().isoformat()
                except Exception:
                    import re
                    m = re.search(r'(\d{4}-\d{2}-\d{2})', txt)
                    if m:
                        date_iso = m.group(1)
            if title:
                out.append({"title": title, "url": url, "snippet": snippet, "date": date_iso})
    except Exception as e:
        logger.debug("parse error: %s", e)
    return out
