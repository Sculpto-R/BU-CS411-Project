import json #to read keyword_rules.json
import re
from pathlib import Path
from django.utils import timezone
from ingestion.models import RawPost
from classification.models import EventCandidate
from datetime import datetime, timedelta

_RULES_CACHE = None

#load_keyword_rules() and suggest_tags(text) power the AI keyword filtering 
#Weight ranks events by relevance, filters out weak signals, and combines scores from genres, locations, and keywords
#Weight helps AI understand which keywords matter more when tagging a post

def load_keyword_rules():
    "Function returns a list of rule dicts from JSON"
    "Looks for keywords and patterns classified in JSON"

    #If rules loaded, return cached copy
    global _RULES_CACHE
    if _RULES_CACHE is not None:
        return _RULES_CACHE
    
    rules_path = Path(__file__).resolve().parent / "data" / "keyword_rules.json"
    
    #Opens JSON file
    f = open(rules_path, "r", encoding = "utf-8") #"r" means open for reading, encoding = "utf-8" handles emojis, accents, etc.
    data = json.load(f)
    f.close()

    for ruleDict in data: #data is a list of dictionaries  [{}] #loop goes through each dictionary (ruleDict)
        for key in ("pattern", "tag", "weight", "category"): #tuple of 4 keys each rule/dictionary has
            if key not in ruleDict: #check if key is missing from rule/dictionary 
                raise ValueError(f"A rule is missing the key:" + key)
    
    _RULES_CACHE = data

    return _RULES_CACHE

def suggest_tags(text): 
    "Function takes text (website event information), goes through keyword rules (JSON file to "
    "find which tags apply) and returns a list of (tag, score) by matching regex rules in the caption text."
   
    "Allows system to understand what each social media post is about -> Converts human text to data"

    if not text:
        return []
    
    rules = load_keyword_rules() #calls other function
    tag_scores = {} #creates empty dictionary to store each tag and its total score ex.{"rave": 1.0, "techno": 0.8}

    for rule in rules:
        pattern = rule["pattern"]
        tag = rule["tag"]
        weight = float(rule.get("weight", 1.0))
    
    #Case-insensitive regex search 
    if re.search(pattern, text, flags = re.IGNORECASE): #uses regex to see if the rule's pattern appears in the text (not case sensitive)
        tag_scores[tag] = tag_scores.get(tag, 0.0) + weight #adds rule's weight to that tag's total score

    #Convert the dict to a list of (tag, score) pairs
    #List sorted highest score first
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
    "jan":1, "january":1,
    "feb":2, "february": 2,
    "mar":3, "march":3,
    "apr":4, "april": 4,
    "may":5, 
    "jun": 6, "june":6,
    "jul":7, "july":7,
    "aug":8, "august":8,
    "sep":9, "september":9,
    "oct":10, "october":10,
    "nov":11, "november":11,
    "dec":12, "december": 12
    }

def parse_time_fragment(text):
    "Turns strings like '10pm' '22:00', '10:30pm' into (hour, minute) 24h."

    text = text.strip().lower()

    m = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$",text)

    if not m:
        return None
    
    hour = int(m.group(1))
    minute = int(m.group(2) or 0)
    ampm = m.group(3)

    #Convert to 24hr if am/pm
    if ampm == "pm" and hour != 12:
        hour += 12
    if ampm == "am" and hour == 12:
        hour = 0
    
    #Ignores weird hours
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None
    
    return (hour, minute)

def guess_base_date(text):
    "Picks a base calender date from the event information."

    text = text.strip().lower()
    now = datetime.now()

    m = re.search(r"\b(\d{1,2})\s*jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|"
                  r"january|february|march|april|june|july|august|september|octoeber|november|december)\b",
                  text, flags = re.IGNORECASE)
    
    if m:
        day = int(m.group(1))
        mon = MONTHS[m.group(2).lower()]
        year = now.year
        try_date = datetime(year, mon, day)

        if (try_date - now).days <-60:
            year += 1
        return datetime(year, mon, day)
    
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", text)

    if m:
        d = int(m.group(1))
        mon = int(m.group(2))
        year = int(m.group(3))
        if year <100:
            year += 2000
        return datetime(year, mon, d)
    
    if "tonight" in text:
        return now
    if "tomorrow" in text:
        return now + timedelta(days = 1)
    
    return now

def find_time_range(text):
    "Finds '10pm-4am' or '22:00-04:00 and returns ((h1,m1), (h2, m2)) or None"

    m = re.search(r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(\d{1,2}(?::d{2})?\s*(?:am|pm)?)",
                  text, flags=re.IGNORECASE)

    if not m:
        return None
    
    time1 = parse_time_fragment(m.group(1))
    time2 = parse_time_fragment(m.group(2))
    
    if time1 and time2:
        return (time1, time2)
    
    return None

def find_single_time(text):
    "Finds a single time like '10pm' or '22:30' and returns (h,m) or None."

    m = re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b", text, flags=re.IGNORECASE )

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
    if singleTime == True:
        h, m = singleTime
        start = base.replace(hour = h, minute = m)
        end = start + timedelta(hours=4) 
        return (start,end)

    #If no time is found stated for event

    return None

def extract_venue(text):
    "Extracts venue(address) information from website event information."

    #if there is no text
    if text == '':
        return {"postcode": None, "area": None, "name": None}

    words = text.split() #splits event information (seperates by words)
    postcode = None
    area = None
    name = None

    londonAreas = ["dalston", "peckham", "brixton", "shoreditch", 
                   "camden", "deptford", "hackney", "soho", "islington", 
                   "clapham", "stratford", "notting", "elephant", "bethnal", "angel"] #have to update

    for word in words:
        w = word.lower()

        #Postcode
        #If the word has at least 2 characters and the first is a letter and the second is a number
        if len(w) >= 2 and w[0].isalpha and w[1].isdigit():
            postcode = w.upper()

        for areaName in londonAreas:
            if areaName in w:
                area = areaName
                break

    return {"postcode": postcode, "area": area, "name": name}


def score_candidate_quality(extractions): # WORK ON

    if extractions == '':
        return 0.0
    
    score = 0.0
    total = 0.0

    tagScores = extractions.get("tag_scores") or {}
    tagSum = sum(tagScores.values())
    tagComponent = min(tagSum / 3.0, 1.0)
    score += 0.35 * tagComponent 
    total += 0.35

    hasTime = bool(extractions.get("start") and extractions.get("end"))
    score += 0.25 * (1.0 if hasTime else 0.0)
    total += 0.25

    venue = extractions.get("venue") or {}
    hasPostcode = bool(venue.get("postcode"))
    hasArea = bool(venue.get("area"))
    venueComponent = 1.0 if hasPostcode else (0.5 if hasArea else 0.0)
    score += 0.20 * venueComponent
    total += 0.20

    hasPrice = ((extractions.get("price_min") is not None) or (extractions.get("price_max") is not None))
    hasAge = bool(extractions.get("age"))
    score += 0.10 * (1.0 if hasPrice else 0.0)
    score += 0.10 * (1.0 if hasAge else 0.0)
    total += 0.20

    if total > 0:
        score = score/total
    if score < 0.0:
        score = 0.0
    if score > 1.0:
        score = 1.0

    return 

def build_event_candidate(rawPostID): #WORK ON

    raw = RawPost.objects.get(pk = rawPostID)
    text = raw.caption or ""

    tagPairs = suggest_tags(text)
    tagScores = dict(tagPairs)
    tags = [t for t, _ in tagPairs]

    pa = extract_price_and_age(text)
    dt = extract_datetime(text)
    venue = extract_venue(text)

    startISO = dt[0].isoformat() if dt else None
    endISO = dt[1].isoformat() if dt else None

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

    score = score_candidate_quality(extractions)

    hasPlace = bool(venue.get("postcode") or venue.get("area"))
    needsReview = not(score >= 0.75 and startISO and hasPlace)

    candidate = EventCandidate.objects.create(
        raw_post = raw,
        extracted_json = extractions,
        score = score,
        needs_review = needsReview,
    )

    return candidate.id

def needs_human_review(candidate, threshold=0.6):
    return 

def match_to_existing_event(candidate_id):
    return

def promote_candidate_to_event(candidate_id):
    return 
