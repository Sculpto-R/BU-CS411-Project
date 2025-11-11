import csv
import json

from django.core.management.base import BaseCommand, CommandError

from ingestion.models import RawPost
from classification.services import build_event_candidate, promote_candidate_to_event
from classification.models import EventCandidate


class Command(BaseCommand):
    help = (
        "Import scraped events from a CSV file into RawPost. "
        "Optionally build AI EventCandidates and promote them to API Events."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            required=True,
            help="Path to the CSV file (e.g. data_scripts/event_scraping/events_out.csv)",
        )
        parser.add_argument(
            "--source",
            required=True,
            help="Source name label (e.g. 'event_scraper_test')",
        )
        parser.add_argument(
            "--build-candidates",
            action="store_true",
            help="After import, run AI extraction to create EventCandidate records.",
        )
        parser.add_argument(
            "--promote",
            action="store_true",
            help="After building candidates, promote them to API Events.",
        )

    def handle(self, *args, **options):
        path = options["path"]
        source = options["source"]
        build_candidates = options["build_candidates"]
        promote = options["promote"]

        try:
            f = open(path, newline="", encoding="utf-8")
        except OSError as e:
            raise CommandError(f"Could not open {path}: {e}")

        created = 0
        created_rawpost_ids = []

        with f:
            reader = csv.DictReader(f)
            for row in reader:
                # Basic fields from CSV
                title = row.get("title") or row.get("event_title") or ""
                desc = row.get("description") or ""
                venue = row.get("venue_name") or row.get("venue") or ""
                address = row.get("address") or ""
                start = (
                    row.get("start_datetime")
                    or row.get("start_time")
                    or row.get("start")
                    or row.get("start_local")
                    or ""
                )

                # Price info
                price_min = row.get("price_min") or ""
                price_max = row.get("price_max") or ""

                price_text = ""
                if price_min and price_max:
                    price_text = f"Prices from £{price_min} to £{price_max}"
                elif price_min:
                    price_text = f"Price £{price_min}"
                elif price_max:
                    price_text = f"Up to £{price_max}"

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
                created_rawpost_ids.append(post.id)
                self.stdout.write(self.style.SUCCESS(f"Created RawPost {post.id}"))

        self.stdout.write(
            self.style.SUCCESS(f"Imported {created} events from {path}")
        )

        # --- Optional: build AI candidates ---
        if build_candidates and created_rawpost_ids:
            self.stdout.write(self.style.WARNING("Building AI EventCandidates..."))
            candidate_ids = []
            for rp_id in created_rawpost_ids:
                cid = build_event_candidate(rp_id)
                candidate_ids.append(cid)
                self.stdout.write(
                    self.style.SUCCESS(f"  Built EventCandidate {cid} from RawPost {rp_id}")
                )

            # --- Optional: promote to API Events ---
            if promote and candidate_ids:
                self.stdout.write(self.style.WARNING("Promoting candidates to API Events..."))
                for cid in candidate_ids:
                    ev_id = promote_candidate_to_event(cid)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Promoted EventCandidate {cid} → Event {ev_id}"
                        )
                    )


