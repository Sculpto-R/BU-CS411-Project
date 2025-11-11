import json #to read keyword_rules.json
import re
from pathlib import Path
from django.utils import timezone
from ingestion.models import RawPost
from classification.models import EventCandidate
from datetime import datetime, timedelta
from api.models import Event

_RULES_CACHE = None

#load_keyword_rules() and suggest_tags(text) power the AI keyword filtering 
#Weight ranks events by relevance, filters out weak signals, and combines scores from genres, locations, and keywords
#Weight helps AI understand which keywords matter more when tagging a post

def load_keyword_rules():
    """
    Returns a list of rule dicts from JSON.
    Caches rules in memory after first load.
    """
    global _RULES_CACHE
    if _RULES_CACHE is not None:
        return _RULES_CACHE

    rules_path = Path(__file__).resolve().parent / "data" / "keyword_rules.json"

    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[load_keyword_rules] ERROR reading {rules_path}: {e}")
        _RULES_CACHE = []
        return _RULES_CACHE

    for i, ruleDict in enumerate(data):
        for key in ("pattern", "tag", "weight", "category"):
            if key not in ruleDict:
                raise ValueError(f"Rule at index {i} is missing the key: {key}")

    _RULES_CACHE = data
    return _RULES_CACHE

def suggest_tags(text):
    """
    Takes event text, applies regex-based keyword rules, and returns a list of
    (tag, score) pairs sorted by score descending.
    """
    if not text:
        return []

    rules = load_keyword_rules()
    tag_scores = {}

    for rule in rules:
        pattern = rule["pattern"]
        tag = rule["tag"]
        weight = float(rule.get("weight", 1.0))

        # Case-insensitive regex search with safety
        try:
            if re.search(pattern, text, flags=re.IGNORECASE):
                tag_scores[tag] = tag_scores.get(tag, 0.0) + weight
        except re.error as e:
            # If a pattern is invalid (e.g. unbalanced parenthesis), skip it
            print(f"[suggest_tags] Skipping bad regex for tag {tag!r}: {pattern!r} ({e})")
            continue

    # Convert dict to sorted list of (tag, score)
    return sorted(tag_scores.items(), key=lambda kv: kv[1], reverse=True)

def extract_price_and_age(text):
    "Extracts price and age information from website event information."

    #if there is no text
    if text == '':
        return {"price_min": None, "price_max": None, "age": None}

    words = text.split() #splits event information (seperates by words)
    prices = [] #initialize list that stores all prices listed for event
    age = None #initialize age variable that will store age requirement for event

    #loop reads event information
    for word in words:
        w = word.lower()

        #Price Checker
        if "£" in w:

            #builds event price
            num = ""
           
            for ch in w:
                if ch.isdigit() or ch == ".":
                    num += ch
            
            if num:
                prices.append(float(num))

        #British monetary slang
        elif "fiver" in w:
            prices.append(5.0)
        
        elif "tenner" in w:
            prices.append(10.0)
        
        elif "free" in w:
            prices.append(0.0)
        
        #Age checker
        if "18+" in w:
            age = "18+"
        
        elif "21+" in w:
            age = "21+"
    
    #Min and max price checker if more than one price is listed
    if prices != []:
        price_min = min(prices)
        price_max = max(prices)
    
    else:
        price_min = None
        price_max = None
   
    return {"price_min": price_min, "price_max": price_max, "age": age}

#For extract_datetime
MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


def parse_time_fragment(text):
    "Turns strings like '10pm' '22:00', '10:30pm' into (hour, minute) 24h."

    text = text.strip().lower()

    #Use regex to find parts of the time:
    #(\d{1,2}) finds 1 or 2 digits for the hour (like '10' or '22')
    #(?::(\d{2}))? finds colon + 2 digits for minutes (like ':30')
    #\s*(am|pm)?$ finds 'am' or 'pm'
    m = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$",text)

    #If no match then no time is returned
    if not m:
        return None
    
    #convert the text found into numbers
    hour = int(m.group(1))
    minute = int(m.group(2) or 0) #if missing use 0
    ampm = m.group(3)

    #Convert to 24hr if am/pm
    if ampm == "pm" and hour != 12:
        hour += 12
    if ampm == "am" and hour == 12:
        hour = 0
    
    #Ignores invalid hours
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None
    
    return (hour, minute)

def guess_base_date(text):
    "Picks a base calendar date from the event information."

    text = (text or "").strip().lower()
    now = datetime.now()  # current date/time as default

    # 1) Named month formats like '12 Oct', '12 October'
    m = re.search(
        r"\b(\d{1,2})\s*"
        r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|"
        r"january|february|march|april|may|june|july|august|september|october|november|december)\b",
        text,
        flags=re.IGNORECASE,
    )

    if m:
        day = int(m.group(1))
        mon = MONTHS[m.group(2).lower()]
        year = now.year
        try_date = datetime(year, mon, day)

        # if the date is more than 2 months in the past, assume next year
        if (try_date - now).days < -60:
            year += 1
        return datetime(year, mon, day)

    # 2) Numeric formats like '12/10', '12-10', '12/10/24', '12-10-2025'
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", text)
    if m:
        d = int(m.group(1))
        mon = int(m.group(2))
        year_str = m.group(3)

        # sanity check: must look like a real calendar date
        if not (1 <= mon <= 12 and 1 <= d <= 31):
            m = None
        else:
            if year_str:
                year = int(year_str)
                if year < 100:
                    year += 2000
            else:
                year = now.year

            return datetime(year, mon, d)

    # 3) Relative words
    if "tonight" in text:
        return now
    if "tomorrow" in text:
        return now + timedelta(days=1)

    # Fallback: current date/time
    return now



def find_time_range(text):
    "Finds '10pm-4am' or '22:00-04:00' and returns ((h1,m1), (h2, m2)) or None"

    m = re.search(
        r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*[-–]\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
        text,
        flags=re.IGNORECASE,
    )
    if not m:
        return None

    time1 = parse_time_fragment(m.group(1))
    time2 = parse_time_fragment(m.group(2))

    if time1 and time2:
        return (time1, time2)
    return None


def find_single_time(text):
    "Finds a single time like '10pm' or '22:30' and returns (h,m) or None."

    #Regex searches for a single time
    m = re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b", text, flags=re.IGNORECASE )

    #If no match found returns none
    if not m:
        return None
    
    return parse_time_fragment(m.group(1))

def extract_datetime(text): 
    "Extracts date and time information from website event information."

    if text == '':
        return None
    
    base = guess_base_date(text)

    #Finds a time range if there is a time range stated for event
    range = find_time_range(text)
    if range:
        (hour1, minute1), (hour2,minute2) = range
        start = base.replace(hour = hour1, minute = minute1)
        end = base.replace(hour= hour2, minute = minute2)
        
        #Event passes through midnight
        if end <=start:
            end += timedelta(days = 1)
        return (start, end)

    #Finds a single time if there is a single time stated for event
    singleTime = find_single_time(text)
    if singleTime:
        h, m = singleTime
        start = base.replace(hour=h, minute=m)
        end = start + timedelta(hours=4)
        return (start, end)

    #If no time is found stated for event

    return None

UK_POSTCODE_RE = re.compile(
    r"\b([A-Z]{1,2}\d{1,2}[A-Z]?)\s*(\d[A-Z]{2})\b",
    re.IGNORECASE,
)

def extract_venue(text):
    """
    Extracts venue info (postcode, area/town, and name) from the caption.
    Assumes the caption is like:
      title | description | venue_name | address | Starts... | Prices...
    """
    if not text:
        return {"postcode": None, "area": None, "name": None}

    parts = [p.strip() for p in text.split("|")]

    venue_name = parts[2] if len(parts) >= 3 else None
    address = parts[3] if len(parts) >= 4 else ""

    postcode = None
    area = None

    # 1) Postcode from the address
    m = UK_POSTCODE_RE.search(address)
    if m:
        postcode = (m.group(1) + m.group(2)).upper()

    # 2) Try to guess town/area from address
    # e.g. "Selsfield Road, Haywards Heath, RH17 6TL, Haywards Heath, RH17 6TL"
    addr_bits = [b.strip() for b in address.split(",") if b.strip()]
    if addr_bits:
        # Heuristic: second-to-last or third-to-last piece is often the town
        for candidate in reversed(addr_bits):
            # Skip pure postcodes
            if UK_POSTCODE_RE.search(candidate):
                continue
            if any(ch.isalpha() for ch in candidate):
                area = candidate
                break

    return {"postcode": postcode, "area": area, "name": venue_name}


def score_candidate_quality(extractions): 
    '''Function takes all extracted event information (tags, price, time, venue, etc.) and calculates
    a confidence score between 0.0 (low confidence) and 1.0 (high confidence)'''

    #If extraction dictionary is empty or invalid, cannot score
    if extractions == '':
        return 0.0
    
    #Initialize score counters
    score = 0.0 #current total confidence score
    total = 0.0 #maximum possible score weight

    #Pulls out all tag scores (ex. {"techno":1.0})
    tagScores = extractions.get("tag_scores") or {}

    #Add up the numeric weights of all matched tags
    tagSum = sum(tagScores.values())
    
    #Normalize tags
    tagComponent = min(tagSum / 3.0, 1.0)

    #Add the weighted tag score
    score += 0.35 * tagComponent 
    total += 0.35

    #Check if both start and end times exist in the extracted data
    hasTime = bool(extractions.get("start") and extractions.get("end"))

    #Give 0.25 credit 
    score += 0.25 * (1.0 if hasTime else 0.0)
    total += 0.25

    #Extract venue data
    venue = extractions.get("venue") or {}

    #Check if venue has a postcode or an area name
    hasPostcode = bool(venue.get("postcode"))
    hasArea = bool(venue.get("area"))

    venueComponent = 1.0 if hasPostcode else (0.5 if hasArea else 0.0)

    score += 0.20 * venueComponent
    total += 0.20

    #Check if price and age restriction are mentioned
    hasPrice = ((extractions.get("price_min") is not None) or (extractions.get("price_max") is not None))
    hasAge = bool(extractions.get("age"))
    
    score += 0.10 * (1.0 if hasPrice else 0.0)
    score += 0.10 * (1.0 if hasAge else 0.0)
    total += 0.20

    #Divide by total so everything adds up to a 0-1 scale
    if total > 0:
        score = score/total
    
    #Ensure score within range
    if score < 0.0:
        score = 0.0
    if score > 1.0:
        score = 1.0

    return score

def build_event_candidate(rawPostID): 
    """Function pulls a a raw event by its ID, runs all AI extractors, builds a JSON-like dictionary"
    of extracted data, calculates the confidence score, and saves everythign as a new EventCandidate object in the database."""

    #Gets the raw event 
    raw = RawPost.objects.get(pk = rawPostID)
    text = raw.caption or ""

    #Extracts keywords/tags
    tagPairs = suggest_tags(text)
    tagScores = dict(tagPairs)
    tags = [t for t, _ in tagPairs] #list of tag names

    #Extracts structured data
    pa = extract_price_and_age(text)
    dt = extract_datetime(text)
    venue = extract_venue(text)

    #Formats dateime fields for JSON storage
    startISO = dt[0].isoformat() if dt else None
    endISO = dt[1].isoformat() if dt else None

    #Combines everything into one dictionary
    extractions = {
        "tags": tags,
        "tag_scores": tagScores,
        "price_min": pa.get("price_min"),
        "price_max": pa.get("price_max"),
        "age": pa.get("age"),
        "start": startISO,
        "end": endISO,
        "venue": venue,
    }

    #Computes the candidate's overall guality score
    score = score_candidate_quality(extractions)

    #Decides if human review is needed 
    hasPlace = bool(venue.get("postcode") or venue.get("area")) #If score is high, found both date/time and venue then AI approved
    needsReview = not(score >= 0.75 and startISO and hasPlace) #flagged if needs review

    #Creates EventCandidate record
    candidate = EventCandidate.objects.create(
        raw_post = raw, #link to original event
        extracted_json = extractions, #All AI data stored in JSON field
        score = score, #confidence level (0-1)
        needs_review = needsReview, #does it need a manual check?
    )

    return candidate.id

def needs_human_review(candidate, threshold=0.6):
    return 

def match_to_existing_event(candidate_id):
    return

def promote_candidate_to_event(candidate_id):

    cand = EventCandidate.objects.get(pk=candidate_id)
    data = cand.extracted_json or {}
    venue = data.get("venue") or {}
    location = venue.get("area") or venue.get("postcode")

    # tags from the extraction
    tags = data.get("tags") or []

    # nicer title: join tags into readable words, e.g. "Film Festival London"
    if tags:
        title_parts = [t.replace("-", " ").title() for t in tags]
        title = " ".join(title_parts)
    else:
        # fallback: use first part of caption or default
        title = (cand.raw_post.caption or "").split("|")[0] or "Untitled Event"

    ev = Event.objects.create(
        title=title,
        description=cand.raw_post.caption or "",
        date_start=data.get("start"),
        date_end=data.get("end"),
        location=location,
        price_min=data.get("price_min"),
        price_max=data.get("price_max"),
        age_restriction=data.get("age"),
        ai_score=cand.score,
        ai_tags=tags, 
    )

    return ev.id

