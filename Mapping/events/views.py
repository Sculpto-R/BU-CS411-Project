from django.shortcuts import render

def index(request):
    # Sample events data
    events_data = [
    {
        "name": "iNNiT Launch Party",
        "address": "10 Downing Street, London",
        "date": "2025-11-01",
        "lat": 51.5034,
        "lng": -0.1276
    },
    {
        "name": "Pride Meetup",
        "address": "Regent's Park, London",
        "date": "2025-11-05",
        "lat": 51.5313,
        "lng": -0.1569
    },
    {
        "name": "Tech Talk",
        "address": "King's Cross Station, London",
        "date": "2025-11-10",
        "lat": 51.5308,
        "lng": -0.1238
    },
    {
        "name": "Art Exhibition",
        "address": "Tate Modern, Bankside, London",
        "date": "2025-11-12",
        "lat": 51.5076,
        "lng": -0.0994
    },
    {
        "name": "Music Festival",
        "address": "Hyde Park, London",
        "date": "2025-11-15",
        "lat": 51.5073,
        "lng": -0.1657
    },
    {
        "name": "Startup Networking",
        "address": "Shoreditch, London",
        "date": "2025-11-18",
        "lat": 51.5246,
        "lng": -0.0717
    },
    {
        "name": "Food Market",
        "address": "Borough Market, London",
        "date": "2025-11-20",
        "lat": 51.5055,
        "lng": -0.0917
    }
]

    
    return render(request, "events/map.html", {"events": events_data})
