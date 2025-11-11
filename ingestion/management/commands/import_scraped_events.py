import csv
import json

from django.core.management.base import BaseCommand, CommandError
from ingestion.models import RawPost  # make sure RawPost is defined here


class Command(BaseCommand):
    help = "Import events from data_scripts/event_scraping/events_out.csv as RawPost rows"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default="data_scripts/event_scraping/events_out.csv",
            help="Path to the scraped events CSV file",
        )
        parser.add_argument(
            "--source",
            default="event_scraper",
            help="Value to store in RawPost.source (for tracking)",
        )

    def handle(self, *args, **options):
    path = options["path"]
    source = options["source"]

    try:
        f = open(path, newline="", encoding="utf-8")
    except OSError as e:
        raise CommandError(f"Could not open {path}: {e}")

    created = 0

    with f:
        reader = csv.DictReader(f)

        for row in reader:
            title = row.get("title") or row.get("event_title") or ""
            desc = row.get("description") or ""
            venue = row.get("venue_name") or row.get("venue") or ""
            address = row.get("address") or ""
            start = (
                row.get("start_datetime")
                or row.get("start_time")
                or row.get("start_local")   # your CSV uses start_local
                or row.get("start")
                or ""
            )

            # 👇 pull numeric prices from CSV
            price_min = row.get("price_min") or ""
            price_max = row.get("price_max") or ""

            # 👇 build a human-readable price snippet
            price_text = ""
            if price_min and price_max:
                price_text = f"Prices from £{price_min} to £{price_max}"
            elif price_min:
                price_text = f"Price £{price_min}"
            elif price_max:
                price_text = f"Up to £{price_max}"

            # 👇 SINGLE parts list – includes price_text
            parts = [
                title,
                desc,
                venue,
                address,
                f"Starts: {start}" if start else "",
                price_text,
            ]

            caption = " | ".join(p for p in parts if p)

            raw_json = json.dumps(row, ensure_ascii=False)

            post = RawPost.objects.create(
                source=source,
                caption=caption,
                raw_json=raw_json,
            )

            created += 1
            self.stdout.write(self.style.SUCCESS(f"Created RawPost {post.id}"))

    self.stdout.write(
        self.style.SUCCESS(f"Imported {created} events from {path}")
    )

