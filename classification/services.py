import json #to read keyword_rules.json
import re
from pathlib import Path

_RULES_CACHE = None

#load_keyword_rules() and suggest_tags(text) power the AI keyword filtering 
#Weight ranks events by relevance, filters out weak tags, and combines scores from genres, locations, and keywords
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
    "Function takes text (captions), goes through keyword rules (JSON file to "
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
    return 

def extract_datetime(text, tz="Europe/London"):
    return 

def extract_venue(text):
    return 

def score_candidate_quality(extractions):
    return 

def build_event_candidate(raw_post_id):
    return 

def needs_human_review(candidate, threshold=0.6):
    return 

def match_to_existing_event(candidate_id):
    return

def promote_candidate_to_event(candidate_id):
    return 
