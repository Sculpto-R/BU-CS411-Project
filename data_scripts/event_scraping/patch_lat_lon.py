#!/usr/bin/env python3
"""
patch_lat_lon.py

Hard-code latitude/longitude for specific snapshot events
by matching on source_url (the HTML snapshot path).

Usage:
    python3 data_scripts/event_scraping/patch_lat_lon.py
"""

import csv

CSV_PATH = "data_scripts/event_scraping/events_out.csv"
OUTPUT_PATH = "data_scripts/event_scraping/events_out_patched.csv"

# 👇 Set approximate coordinates per snapshot file
# (You can tweak these if you want more precise values later.)
SNAPSHOT_COORDS = {
    "snapshots/shoreham.html": ("50.8340", "-0.2740"),   # Shoreham-by-Sea approx
    "snapshots/jazz.html": ("51.5176", "-0.1180"),       # Central London (Holborn-ish)
    "snapshots/mura.html": ("51.5136", "-0.1365"),       # Soho-ish
    "snapshots/gallery.html": ("51.5220", "-0.0715"),    # Shoreditch-ish
}


def patch_coords():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    if "source_url" not in fieldnames or "latitude" not in fieldnames or "longitude" not in fieldnames:
        raise SystemExit("CSV must contain 'source_url', 'latitude', and 'longitude' columns.")

    updated = 0

    for row in rows:
        src = row.get("source_url", "")
        # We only care about snapshot-based rows
        for key, (lat, lon) in SNAPSHOT_COORDS.items():
            if key in src:
                row["latitude"] = lat
                row["longitude"] = lon
                updated += 1

    print(f"Patched coordinates for {updated} row(s).")

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Done. Wrote patched CSV to: {OUTPUT_PATH}")


if __name__ == "__main__":
    patch_coords()


