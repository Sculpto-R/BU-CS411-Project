#!/usr/bin/env python3
"""
patch_event_ids.py

Set event_id for specific snapshot-based events (jazz, mura, gallery)
in events_out.csv.

Usage:
    python3 data_scripts/event_scraping/patch_event_ids.py
"""

import csv

CSV_PATH = "data_scripts/event_scraping/events_out.csv"
OUTPUT_PATH = "data_scripts/event_scraping/events_out_patched.csv"

EVENT_ID_PATCHES = {
    "data_scripts/event_scraping/snapshots/jazz.html": "jazz-snap-london-1",
    "data_scripts/event_scraping/snapshots/mura.html": "mura-snap-london-1",
    "data_scripts/event_scraping/snapshots/gallery.html": "gallery-snap-london-1",
}


def main():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    if "event_id" not in fieldnames:
        fieldnames.insert(0, "event_id")  # ensure event_id column exists as first col

    updated = 0

    for row in rows:
        src = row.get("source_url", "")
        if src in EVENT_ID_PATCHES:
            row["event_id"] = EVENT_ID_PATCHES[src]
            updated += 1

    print(f"Patched event_id for {updated} row(s).")

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote patched CSV to: {OUTPUT_PATH}")
    print("If it looks good, replace events_out.csv with this file.")


if __name__ == "__main__":
    main()


