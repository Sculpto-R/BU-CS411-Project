"""
multi_site_event_scraper.py
Scrape events from many venue sites into one normalized CSV.

Strategy:
1) Prefer JSON-LD (schema.org/Event) if present.
2) Else use per-site CSS selectors in SITE_PROFILES.

Usage:
  python3 data_scripts/event_scraping/multi_site_event_scraper.py \
    --out data_scripts/event_scraping/events_out.csv \
    https://www.galleryclublondon.com/whatson
"""
import argparse, csv, json, os, re, time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dparser

CSV_HEADERS = [
    "event_id","source_url","source_site","venue_name","venue_url","event_title","category","tags",
    "start_local","end_local","timezone","start_utc","end_utc","city","address","latitude","longitude",
    "price_currency","price_min","price_max","is_free","booking_url","image_url","description",
    "accessibility","age_restrictions","organizer","updated_at_utc","scraped_at_utc","data_license","notes",
]

SITE_PROFILES: Dict[str, Dict[str, str]] = {
    # Add per-domain selectors here when JSON-LD is missing, e.g.:
    # "www.southbankcentre.co.uk": {"card":"li.teaser","title":".teaser__title","date":".teaser__date","link":"a","img":"img"},
    # "www.barbican.org.uk": {"card":".promo","title":".promo__title","date":".promo__meta","link":"a","img":"img"},
    # "www.galleryclublondon.com": {"card":".event-card","title":".event-title","date":".event-date","link":"a","img":"img"},
}

@dataclass
class EventRow:
    event_id: str = ""
    source_url: str = ""
    source_site: str = ""
    venue_name: str = ""
    venue_url: str = ""
    event_title: str = ""
    category: str = ""
    tags: str = ""
    start_local: str = ""
    end_local: str = ""
    timezone: str = "Europe/London"
    start_utc: str = ""
    end_utc: str = ""
    city: str = "London"
    address: str = ""
    latitude: str = ""
    longitude: str = ""
    price_currency: str = "GBP"
    price_min: str = ""
    price_max: str = ""
    is_free: str = ""
    booking_url: str = ""
    image_url: str = ""
    description: str = ""
    accessibility: str = ""
    age_restrictions: str = ""
    organizer: str = ""
    updated_at_utc: str = ""
    scraped_at_utc: str = ""
    data_license: str = "Coursework use; see site terms"
    notes: str = ""
    def finalize(self) -> Dict[str, str]:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if not self.updated_at_utc: self.updated_at_utc = now
        if not self.scraped_at_utc: self.scraped_at_utc = now
        return {k: getattr(self, k) for k in CSV_HEADERS}

def http_get(url: str) -> str:
    headers = {"User-Agent":"Mozilla/5.0 (compatible; CS411MultiSiteScraper/1.0)"}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.text

def clean_text(s: Optional[str]) -> str:
    if not s: return ""
    return re.sub(r"\s+"," ",s).strip()

def to_local_iso(dt_str: Optional[str]) -> str:
    if not dt_str: return ""
    try:
        dt = dparser.parse(dt_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return clean_text(dt_str)

def shortlist(text: str, limit=280) -> str:
    t = clean_text(text)
    return t if len(t)<=limit else t[:limit-1]+"…"

def guess_event_id(venue_name: str, title: str, start_local: str) -> str:
    base = f"{venue_name}|{title}|{start_local}"
    return re.sub(r"[^a-z0-9]+","-",base.lower()).strip("-")[:80]

def parse_price(offers: Any):
    cur="GBP"; pmin=""; pmax=""; is_free=""
    if isinstance(offers, dict):
        cur = offers.get("priceCurrency",cur) or cur
        price = offers.get("price"); low = offers.get("lowPrice"); high = offers.get("highPrice")
        if price is not None:
            try: pmin=pmax=str(float(price))
            except Exception: pmin=pmax=clean_text(str(price))
        if low is not None: pmin=str(low)
        if high is not None: pmax=str(high)
        if clean_text(str(offers.get("category",""))).lower()=="free": is_free="true"
    elif isinstance(offers, list) and offers:
        cur,pmin,pmax,is_free = parse_price(offers[0])
    return cur,pmin,pmax,is_free

def extract_jsonld_events(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html,"html.parser"); events=[]
    for tag in soup.find_all("script",{"type":"application/ld+json"}):
        try: data=json.loads(tag.string or "{}")
        except Exception: continue
        def walk(obj):
            if isinstance(obj, dict):
                t=obj.get("@type") or obj.get("type")
                if isinstance(t, list): is_event = "event" in [str(x).lower() for x in t]
                else: is_event = str(t).lower()=="event"
                if is_event: events.append(obj)
                for v in obj.values(): walk(v)
            elif isinstance(obj, list):
                for v in obj: walk(v)
        walk(data)
    return events

def jsonld_to_row(obj: Dict[str, Any], page_url: str, venue_hint: Optional[str]) -> EventRow:
    name=clean_text(obj.get("name")); start=obj.get("startDate"); end=obj.get("endDate")
    location=obj.get("location") or {}
    if isinstance(location,list) and location: location=location[0]
    venue_name=clean_text((location.get("name") if isinstance(location,dict) else "") or (venue_hint or ""))
    address=""
    if isinstance(location,dict):
        addr=location.get("address") or {}
        if isinstance(addr,dict):
            parts=[addr.get(k,"") for k in ["streetAddress","addressLocality","postalCode"]]
            address=clean_text(", ".join([p for p in parts if p]))
    currency,pmin,pmax,is_free = parse_price(obj.get("offers",{}))
    img=obj.get("image"); 
    if isinstance(img,list): img = img[0] if img else ""
    desc=shortlist(obj.get("description",""))
    organizer=""
    org=obj.get("organizer")
    if isinstance(org,dict): organizer=clean_text(org.get("name",""))
    booking_url=obj.get("url") or page_url
    row = EventRow(
        event_title=name,
        start_local=to_local_iso(start), end_local=to_local_iso(end),
        venue_name=venue_name,
        venue_url=f"{urlparse(page_url).scheme}://{urlparse(page_url).netloc}",
        source_url=page_url, source_site=urlparse(page_url).netloc,
        category=clean_text(obj.get("@type","Event")),
        description=desc, price_currency=currency, price_min=str(pmin), price_max=str(pmax),
        is_free=is_free, booking_url=booking_url, image_url=clean_text(img or ""),
        organizer=organizer, address=address
    )
    row.event_id = guess_event_id(row.venue_name or row.source_site, row.event_title, row.start_local)
    return row

def extract_with_selectors(html: str, page_url: str, venue_hint: Optional[str]) -> List[EventRow]:
    host=urlparse(page_url).netloc
    profile=SITE_PROFILES.get(host)
    if not profile: return []
    soup=BeautifulSoup(html,"html.parser")
    rows: List[EventRow]=[]
    for card in soup.select(profile["card"]):
        title=""; date_text=""; href=page_url; img=""
        if profile.get("title"):
            t=card.select_one(profile["title"]); title=clean_text(t.get_text(strip=True)) if t else ""
        if profile.get("date"):
            d=card.select_one(profile["date"]); date_text=clean_text(d.get_text(" ",strip=True)) if d else ""
        if profile.get("link"):
            a=card.select_one(profile["link"])
            if a and a.has_attr("href"): href=urljoin(page_url,a["href"])
        if profile.get("img"):
            it=card.select_one(profile["img"])
            if it and it.has_attr("src"): img=urljoin(page_url,it["src"])
        row=EventRow(
            event_title=title, start_local=to_local_iso(date_text),
            venue_name=venue_hint or host,
            venue_url=f"{urlparse(page_url).scheme}://{host}",
            source_url=page_url, source_site=host,
            booking_url=href, image_url=img, description="", notes="CSS fallback"
        )
        row.event_id = guess_event_id(row.venue_name or row.source_site, row.event_title, row.start_local)
        rows.append(row)
    return rows

def scrape_page(url: str, venue_hint: Optional[str]) -> List[EventRow]:
    html=http_get(url); rows: List[EventRow]=[]
    for obj in extract_jsonld_events(html):
        try: rows.append(jsonld_to_row(obj,url,venue_hint))
        except Exception: continue
    if not rows: rows = extract_with_selectors(html,url,venue_hint)
    if not rows:
        host=urlparse(url).netloc
        rows=[EventRow(
            source_url=url, source_site=host, venue_name=venue_hint or host,
            venue_url=f"{urlparse(url).scheme}://{host}", event_title="(No events found)",
            notes="No JSON-LD and no SITE_PROFILES selectors for this domain"
        )]
    return rows

def write_rows(path: str, rows: List[EventRow], append=False):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    mode="a" if append and os.path.exists(path) else "w"
    with open(path, mode, newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if mode=="w": w.writeheader()
        for r in rows: w.writerow(r.finalize())

def main():
    ap=argparse.ArgumentParser(description="Scrape multiple venue pages into a normalized CSV.")
    ap.add_argument("urls", nargs="+", help="One or more event listing URLs")
    ap.add_argument("--venue", default="", help="Optional venue name override")
    ap.add_argument("--out", default="data_scripts/event_scraping/events_out.csv", help="Output CSV path")
    ap.add_argument("--append", action="store_true", help="Append to existing CSV")
    ap.add_argument("--delay", type=float, default=1.5, help="Delay seconds between pages")
    args=ap.parse_args()

    all_rows: List[EventRow]=[]
    for i,url in enumerate(args.urls,1):
        try:
            rows=scrape_page(url, args.venue or None)
            all_rows.extend(rows)
            print(f"[{i}/{len(args.urls)}] {url} -> {len(rows)} row(s)")
        except Exception as e:
            print(f"[{i}/{len(args.urls)}] {url} -> ERROR: {e}")
        time.sleep(max(0.0,args.delay))

    write_rows(args.out, all_rows, append=args.append)
    print(f"Wrote {len(all_rows)} row(s) to {args.out}")

if __name__=="__main__":
    main()
  
# Also write to JSON for map integration
import json
json_out_path = args.out.replace(".csv", ".json")
with open(json_out_path, "w", encoding="utf-8") as jf:
    json.dump([r.finalize() for r in all_rows], jf, ensure_ascii=False, indent=2)
print(f"Wrote JSON to {json_out_path}")


