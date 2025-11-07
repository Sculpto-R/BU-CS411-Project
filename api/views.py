from django.shortcuts import render
import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

#import services
from classification.services import (
    suggest_tags, extract_price_and_age, extract_datetime, 
    extract_venue, score_candidate_quality
)

@csrf_exempt
def classify_preview(request):
    """
        Post {"text": "caption"} --> JSON with tags, price, age, datetime, vanue, score}
    """

    if request.method != "POST":
        return HttpResponseBadRequest("Use POST with JSON{'text':'...'}")

    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON body")

    text = (body.get("text") or "").strip()
    if text =="":
        return HttpResponseBadRequest("Missing 'text'")
    
    tag_pairs = suggest_tags(text)
    tag_scores = dict(tag_pairs)
    tags = [t for t, _ in tag_pairs]

    pa = extract_price_and_age(text)
    dt = extract_datetime(text)
    venue = extract_venue(text)

    startISO = dt[0].isoformat() if dt else None
    endISO = dt[1].isoformat() if dt else None

    payload = {
        "tags": tags,
        "tag_scores": tag_scores,
        "price_min": pa.get("price_min"),
        "price_max": pa.get("price_max"),
        "age": pa.get("age"),
        "start": startISO,
        "end": endISO,
        "venue": venue,
    }

    score = score_candidate_quality({
        "tag_scores": tag_scores,
        "price_min": pa.get("price_min"),
        "price_max": pa.get("price_max"),
        "age": pa.get("age"),
        "start": startISO,
        "end": endISO,
        "venue": venue,
    })

    payload["score"] = score

    return JsonResponse(payload, status=200)
