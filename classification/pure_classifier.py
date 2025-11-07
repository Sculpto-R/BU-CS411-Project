def classify_caption(text: str):
    """Keyword-based tagger for events."""
    t = (text or "").lower()

    TAG_RULES = {
        "techno": ["techno"],
        "house": ["house music", "house"],
        "dnb": ["dnb", "drum and bass", "drum & bass"],
        "jazz": ["jazz", "ensemble", "quartet"],
        "film": ["film", "screening", "cinema", "movie", "documentary", "banff"],
        "festival": ["festival"],
        "comedy": ["comedy", "stand-up", "standup"],
        "theatre": ["theatre", "theater", "play"],
        "art": ["art show", "exhibition", "gallery"],
        "market": ["market", "fair", "flea"],
        "food": ["food", "street food", "supper club"],
        "talk": ["talk", "lecture", "panel", "q&a", "q & a"],
        "workshop": ["workshop", "class", "course"],
        "family": ["family", "kids", "child-friendly", "all ages"],
        "live": ["live band", "live music", "gig"],
        "club": ["club night", "dj set", "rave"],
        "networking": ["networking", "meetup", "mixer"],
        "free": ["free entry", "free event", "free"],
        "18+": ["18+", "18 plus"],
        "21+": ["21+", "21 plus"],
    }

    tags = []
    for tag, needles in TAG_RULES.items():
        for n in needles:
            if n in t:
                tags.append(tag)
                break

    score = min(len(tags) / 4.0, 1.0)
    return list(dict.fromkeys(tags)), round(score, 3)
