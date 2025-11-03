import logging
from datetime import datetime

# User management
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse

from .forms import AccountForm, DOBForm, PreferencesForm, CustomPasswordChangeForm, ProfileEditForm
from .models import Profile


# Mapping API integration
import math
import requests
from bs4 import BeautifulSoup
from django.http import JsonResponse, HttpResponseBadRequest
from datetime import datetime, date
from django.views.decorators.http import require_GET



# Logger for... logging.
logger = logging.getLogger("accounts")

# Session key to keep registration progress
REG_SESSION_KEY = 'reg_data'

def clear_reg_session(request):
    if REG_SESSION_KEY in request.session:
        del request.session[REG_SESSION_KEY]


def get_reg_data(request):
    return request.session.get(REG_SESSION_KEY, {})


def set_reg_data(request, data):
    request.session[REG_SESSION_KEY] = data
    request.session.modified = True


def landing_page(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'landing.html')



@login_required
def password_change(request):
    """Allow logged-in user to change their password."""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # keep user logged in
            messages.success(request, 'Your password has been changed successfully.')
            logger.info("User %s changed password", request.user.username)
            return redirect('accounts:profile')
        else:
            logger.warning("Password change errors for user %s: %s", request.user.username, form.errors)
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'accounts/password_change.html', {'form': form})


@login_required
def home_screen(request):
    """
    Main homepage with interactive map showing events.
    Pulls from the api_find_events endpoint asynchronously via JS.
    """
    profile = getattr(request.user, 'profile', None)
    prefs = normalize_preferences(profile)
    return render(request, 'home.html', {
        'profile': profile,
        'preferences': prefs,
    })


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_invalid(self, form):
        logger.warning("Invalid login attempt (username=%s)", self.request.POST.get('username'))
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('landing')

    def get(self, request, *args, **kwargs):
        logger.info("Logout requested for user %s via GET", request.user.username if request.user.is_authenticated else "anonymous")
        return self.post(request, *args, **kwargs)


def reg_step1(request):
    """
    Step 1: Intro page. No form — starts the session data.
    """
    # initialize session store
    set_reg_data(request, {})
    progress = 1
    logger.debug("Registration step 1 started; session initialized.")
    return render(request, 'accounts/register_step1.html', {'progress': progress})

def reg_step2(request):
    """
    Step 2: Account info (username, first/last name, email, password + confirmation)
    """
    if request.user.is_authenticated:
        return redirect('home')
    reg_data = get_reg_data(request)
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            reg_data['account'] = {
                'username': form.cleaned_data['username'],
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'email': form.cleaned_data['email'],
                # store password temporarily to create user at the end
                'password': form.cleaned_data['password1'],
            }
            set_reg_data(request, reg_data)
            logger.debug("Registration step 2 saved account info for username=%s", reg_data['account']['username'])
            return redirect('accounts:register_step3')
        else:
            logger.debug("Registration step 2 validation errors: %s", form.errors)
    else:
        # prefill from session if present.
        initial = {}
        if 'account' in reg_data:
            acct = reg_data['account']
            initial = {
                'username': acct.get('username'),
                'first_name': acct.get('first_name'),
                'last_name': acct.get('last_name'),
                'email': acct.get('email'),
            }
        form = AccountForm(initial=initial)
    progress = 2
    return render(request, 'accounts/register_step2.html', {'form': form, 'progress': progress})


def reg_step3(request):
    """
    Step 3: Date of birth (18+)
    """
    if request.user.is_authenticated:
        return redirect('home')
    reg_data = get_reg_data(request)
    if request.method == 'POST':
        form = DOBForm(request.POST)
        if form.is_valid():
            reg_data['dob'] = str(form.cleaned_data['date_of_birth'])
            set_reg_data(request, reg_data)
            logger.debug("Registration step 3 saved dob: %s", reg_data['dob'])
            return redirect('accounts:register_step4')
        else:
            logger.debug("Registration step 3 validation errors: %s", form.errors)
    else:
        initial = {}
        if 'dob' in reg_data:
            initial['date_of_birth'] = reg_data['dob']
        form = DOBForm(initial=initial)
    progress = 3
    return render(request, 'accounts/register_step3.html', {'form': form, 'progress': progress})


def reg_step4(request):
    if request.user.is_authenticated:
        return redirect('home')

    reg_data = get_reg_data(request)

    if request.method == 'POST':
        form = PreferencesForm(request.POST)
        if form.is_valid():
            reg_data['preferences'] = {
                'presets': form.cleaned_data.get('presets', []),
                'custom': form.cleaned_data.get('custom_list', []),
            }
            set_reg_data(request, reg_data)

            acct = reg_data.get('account')
            dob = reg_data.get('dob')
            prefs = reg_data.get('preferences', {})
            if not acct or not dob or not prefs:
                messages.error(request, "Registration data incomplete; please restart registration.")
                return redirect('accounts:register_step1')

            from django.contrib.auth.models import User
            if User.objects.filter(username__iexact=acct['username']).exists():
                messages.error(request, "A user with that username already exists.")
                return redirect('accounts:register_step2')

            from datetime import datetime
            dob_date = datetime.fromisoformat(str(dob)).date()

            user = User.objects.create_user(
                username=acct['username'],
                email=acct['email'],
                password=acct['password'],
                first_name=acct.get('first_name', ''),
                last_name=acct.get('last_name', ''),
            )

            profile = Profile.objects.get(user=user)
            profile.date_of_birth = dob_date
            profile.age_verified = True
            profile.presets = prefs.get('presets', [])
            profile.custom_preferences = prefs.get('custom', [])
            profile.save(update_fields=['date_of_birth', 'age_verified', 'presets', 'custom_preferences'])

            login(request, user)
            clear_reg_session(request)
            return redirect('accounts:welcome')
    else:
        initial = {}
        if 'preferences' in reg_data:
            prefs = reg_data['preferences']
            initial['presets'] = prefs.get('presets', [])
            initial['custom_preferences'] = ', '.join(prefs.get('custom', []))
        form = PreferencesForm(initial=initial)

    return render(request, 'accounts/register_step4.html', {'form': form, 'progress': 4})


@login_required
def welcome(request):
    """Step 5: Welcome page after registration. The user should be logged in here."""
    profile = getattr(request.user, 'profile', None)
    return render(request, 'accounts/welcome.html', {'profile': profile})


@login_required
def profile(request):
    """View and edit profile details (name, email, DOB, preferences, password)."""
    user = request.user
    profile = getattr(user, 'profile', None)

    if request.method == 'POST':
        if 'save_profile' in request.POST:
            form = ProfileEditForm(request.POST, instance=profile, user=user)
            pwd_form = CustomPasswordChangeForm(user)
            if form.is_valid():
                form.save(user=user)
                messages.success(request, "Profile updated successfully.")
                logger.info("Profile updated for user %s", user.username)
                return redirect('accounts:profile')

        elif 'change_password' in request.POST:
            form = ProfileEditForm(user=user, instance=profile)
            pwd_form = CustomPasswordChangeForm(user, request.POST)
            if pwd_form.is_valid():
                pwd_form.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed successfully.")
                logger.info("Password changed (profile view) for user %s", user.username)
                return redirect('accounts:profile')
    else:
        form = ProfileEditForm(user=user, instance=profile)
        pwd_form = CustomPasswordChangeForm(user)

    return render(
        request,
        'accounts/profile.html',
        {'form': form, 'pwd_form': pwd_form, 'profile': profile}
    )


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    from .models import Profile
    try:
        if created:
            profile, created_flag = Profile.objects.get_or_create(user=instance)
            if created_flag:
                logger.info(f"Profile created for new user: {instance.username}")
        else:
            if hasattr(instance, 'profile'):
                instance.profile.save()
                logger.debug(f"Profile updated for user: {instance.username}")
    except IntegrityError as e:
        logger.error(f"Profile creation failed for {instance.username}: {e}")


@login_required
def profile_view(request):
    """Display-only profile. Links to separate edit pages."""
    profile = getattr(request.user, 'profile', None)
    return render(request, 'accounts/profile.html', {'profile': profile})

@login_required
def edit_account(request):
    """Edit username / name / email via ProfileEditForm."""
    profile = getattr(request.user, 'profile', None)
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, "Account information updated.")
            logger.info("Account info updated for user %s", request.user.username)
            return redirect('accounts:profile')
        else:
            logger.debug("Edit account form errors for %s: %s", request.user.username, form.errors)
    else:
        form = ProfileEditForm(instance=profile, user=request.user)
    return render(request, 'accounts/edit_account.html', {'form': form})

@login_required
def edit_dob(request):
    profile = getattr(request.user, 'profile', None)
    if request.method == 'POST':
        form = DOBForm(request.POST)
        if form.is_valid():
            profile.date_of_birth = form.cleaned_data['date_of_birth']
            profile.age_verified = True
            profile.save()
            messages.success(request, "Date of birth updated.")
            logger.info("DOB updated for user %s", request.user.username)
            return redirect('accounts:profile')
        else:
            logger.debug("Edit DOB form errors for %s: %s", request.user.username, form.errors)
    else:
        initial = {}
        if profile and profile.date_of_birth:
            initial['date_of_birth'] = profile.date_of_birth
        form = DOBForm(initial=initial)
    return render(request, 'accounts/edit_dob.html', {'form': form})

@login_required
def edit_preferences(request):
    profile = getattr(request.user, 'profile', None)
    if request.method == 'POST':
        form = PreferencesForm(request.POST)
        if form.is_valid():
            presets = form.cleaned_data['presets']
            custom_list = form.cleaned_data['custom_list']
            profile.presets = presets
            profile.custom_preferences = custom_list
            profile.save()
            messages.success(request, "Preferences updated.")
            logger.info("Preferences updated for user %s: presets=%s custom=%s", request.user.username, presets, custom_list)
            return redirect('accounts:profile')
        else:
            logger.debug("Edit preferences form errors for %s: %s", request.user.username, form.errors)
    else:
        # prefill presets and custom
        initial = {
            'presets': profile.presets or [],
            'custom_preferences': ', '.join(profile.custom_preferences or [])
        }
        form = PreferencesForm(initial=initial)
    return render(request, 'accounts/edit_preferences.html', {'form': form})







def haversine_dist_km(lat1, lon1, lat2, lon2):
    """Return distance in km between two lat/lon points."""
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def normalize_preferences(profile):
    """
    Return a flat list of lowercase preference tokens from profile.
    Accepts lists or comma/string stored preferences.
    """
    prefs = []
    if not profile:
        return prefs
    # presets may be a list or a CSV string
    presets = getattr(profile, 'presets', None)
    custom = getattr(profile, 'custom_preferences', None) or getattr(profile, 'custom_preference', None)

    def coerce_to_list(x):
        if x is None:
            return []
        if isinstance(x, (list, tuple)):
            return [str(i).strip() for i in x if i]
        if isinstance(x, str):
            # try comma-separated
            parts = [p.strip() for p in x.split(',') if p.strip()]
            return parts
        return [str(x)]

    prefs += coerce_to_list(presets)
    prefs += coerce_to_list(custom)
    # normalize and dedupe while preserving order
    seen = set()
    out = []
    for p in prefs:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


# map preference tokens -> OSM search keywords (amenity / tag hints)
OSM_PREFERENCE_KEYWORDS = {
    'party': ['nightclub', 'bar', 'pub'],
    'club': ['nightclub', 'bar'],
    'concert': ['music_venue', 'theatre', 'arts_centre', 'concert_hall'],
    'festival': ['park', 'public_square', 'festival_site', 'stadium'],
    'exhibition': ['museum', 'arts_centre', 'gallery'],
    'meetup': ['community_centre', 'arts_centre'],
    'other': ['venue', 'bar', 'club']
}


def build_overpass_query(interests, around_m=5000, lat=51.5074, lon=-0.1278, max_results=80):
    """
    Build a conservative Overpass QL query that searches for nodes and ways
    that might represent venues matching user interests.
    """
    # flatten keywords from mapping
    keywords = set()
    for it in interests:
        kws = OSM_PREFERENCE_KEYWORDS.get(it, [it])
        for k in kws:
            keywords.add(k)

    # special-case: If keyword is a general token like 'bar' use amenity
    # We'll attempt node and way searches and return basic tags.
    # Surround with bounding ring by radius using around:XX
    conds = []
    for k in keywords:
        # try amenity & tourism & leisure & entertainment keys
        conds.append(f'node["amenity"="{k}"](around:{around_m},{lat},{lon});')
        conds.append(f'node["leisure"="{k}"](around:{around_m},{lat},{lon});')
        conds.append(f'node["tourism"="{k}"](around:{around_m},{lat},{lon});')
        # ways too (we'll return centroid for ways in the result)
        conds.append(f'way["amenity"="{k}"](around:{around_m},{lat},{lon});')
        conds.append(f'way["leisure"="{k}"](around:{around_m},{lat},{lon});')
        conds.append(f'way["tourism"="{k}"](around:{around_m},{lat},{lon});')

    # Build query
    q = "[out:json][timeout:25];(" + "".join(conds) + ");out center %s;" % max_results
    return q


# ---------- main API view ----------
@require_GET
@login_required
def api_find_events(request):
    """
    GET parameters:
      - lat, lon (optional) : center location (defaults to London center)
      - radius (optional) : search radius in meters (default 5000)
    Returns JSON:
      { events: [ { id, title, lat, lon, type, snippet, url, date_iso } ], venues: [...] }
    """
    user = request.user
    profile = getattr(user, 'profile', None)

    # parse params (with sensible defaults)
    try:
        lat = float(request.GET.get('lat', 51.5074))
        lon = float(request.GET.get('lon', -0.1278))
    except Exception:
        return HttpResponseBadRequest("Invalid lat/lon")

    try:
        radius = int(request.GET.get('radius', 5000))
    except Exception:
        radius = 5000

    # build interest tokens from profile (or fallback to defaults)
    interests = normalize_preferences(profile) or ['party', 'club', 'concert']

    # Build Overpass query
    query = build_overpass_query(interests, around_m=radius, lat=lat, lon=lon)

    overpass_url = "https://overpass-api.de/api/interpreter"
    try:
        r = requests.get(overpass_url, params={'data': query}, timeout=20)
        r.raise_for_status()
        osm = r.json()
    except Exception as e:
        logger.warning("Overpass query failed: %s", e)
        osm = {'elements': []}

    # Collect venues
    venues = []
    for el in osm.get('elements', []):
        # element may be node or way; get lat/lon (ways provide center)
        el_lat = el.get('lat') or (el.get('center') or {}).get('lat')
        el_lon = el.get('lon') or (el.get('center') or {}).get('lon')
        if not el_lat or not el_lon:
            continue
        tags = el.get('tags', {}) or {}
        v = {
            'id': el.get('id'),
            'name': tags.get('name', tags.get('brand') or 'Unnamed'),
            'type': tags.get('amenity') or tags.get('leisure') or tags.get('tourism') or 'venue',
            'lat': el_lat,
            'lon': el_lon,
            'tags': tags
        }
        venues.append(v)

    # Basic scraping of a public aggregator to find candidate events (keep it minimal)
    scraped_events = []
    try:
        # lightweight request to an aggregator page (London); change if needed
        ev_res = requests.get("https://allevents.in/london", timeout=10, headers={'User-Agent': 'iNNiT-bot/0.1 (+https://innit.local)'} )
        if ev_res.status_code == 200:
            soup = BeautifulSoup(ev_res.text, "html.parser")
            # site structure may vary; try a couple of selectors gracefully
            cards = soup.select(".event-item, .event-card, .col-event-card") or soup.select(".card") or []
            # Grab top ~40 cards
            for card in cards[:40]:
                # Try to extract title, url, date, and short snippet if available
                title_tag = card.select_one("h3, .card-title, .event-title, a")
                link_tag = card.select_one("a[href]")
                date_tag = card.select_one(".date, time, .event-time")
                snippet_tag = card.select_one(".description, .card-text, .event-desc")
                title = title_tag.get_text(strip=True) if title_tag else None
                url = link_tag['href'] if link_tag and link_tag.get('href') else None
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ''
                date_iso = None
                if date_tag:
                    date_text = date_tag.get_text(" ", strip=True)
                    # try to parse date (many formats); be lenient
                    try:
                        parsed = datetime.fromisoformat(date_text.strip())
                        date_iso = parsed.date().isoformat()
                    except Exception:
                        # fallback: search for YYYY-MM-DD substring
                        import re
                        m = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
                        if m:
                            date_iso = m.group(1)
                if title:
                    scraped_events.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'date': date_iso
                    })
    except Exception as e:
        logger.debug("Event scraping failed (non-fatal): %s", e)

    # Match scraped events to venues (best-effort: name substring / nearest)
    matched_events = []
    for ev in scraped_events:
        # reject past events if date is parseable
        if ev.get('date'):
            try:
                ev_date = datetime.fromisoformat(ev['date']).date()
                if ev_date < date.today():
                    continue
            except Exception:
                pass

        title_low = (ev['title'] or '').lower()
        matched_venue = None
        # First try name substring match
        for v in venues:
            if v['name'] and v['name'].lower() in title_low or title_low in (v['name'] or '').lower():
                matched_venue = v
                break
        # If none, use nearest venue within threshold (2km)
        if not matched_venue and venues:
            # compute distances; choose nearest
            nearest = min(venues, key=lambda x: haversine_dist_km(lat, lon, x['lat'], x['lon']))
            if haversine_dist_km(lat, lon, nearest['lat'], nearest['lon']) <= (radius / 1000.0):
                matched_venue = nearest

        # Decide event type by intersection with interests
        ev_type = None
        for it in interests:
            if it in title_low or it in (ev['snippet'] or '').lower():
                ev_type = it
                break
        if not ev_type:
            ev_type = matched_venue['type'] if matched_venue else 'event'

        # Build event record
        if matched_venue:
            e = {
                'title': ev['title'],
                'url': ev.get('url'),
                'snippet': ev.get('snippet'),
                'date': ev.get('date'),
                'lat': matched_venue['lat'],
                'lon': matched_venue['lon'],
                'venue_name': matched_venue['name'],
                'type': ev_type,
                'source': 'allevents.in'
            }
            matched_events.append(e)

    # Also create pseudo-events from venues (if no scraped match), e.g., upcoming nights
    # We limit to a sample of venues:
    for v in venues[:40]:
        # skip if already have event for this venue
        if any(abs(e['lat'] - v['lat']) < 1e-6 and abs(e['lon'] - v['lon']) < 1e-6 for e in matched_events):
            continue
        # create a lightweight pseudo event — marked as 'venue_suggestion'
        title = f"{v['name']} — {v['type']}"
        e = {
            'title': title,
            'url': None,
            'snippet': f"Venue: {v['name']} ({v['type']})",
            'date': (date.today()).isoformat(),
            'lat': v['lat'],
            'lon': v['lon'],
            'venue_name': v['name'],
            'type': v['type'],
            'source': 'osm'
        }
        matched_events.append(e)
        # limit number to avoid excessive payload
        if len(matched_events) >= 80:
            break

    # Filter only events that match user interests (best-effort)
    filtered = []
    token_set = set(interests)
    for e in matched_events:
        # match event type or any token in title/snippet
        ek = e.get('type', '').lower()
        title_snip = (e.get('title','') + " " + e.get('snippet','')).lower()
        if ek in token_set or any(tok in title_snip for tok in token_set):
            filtered.append(e)
    # fallback: if filtered empty, return matched_events
    if not filtered:
        filtered = matched_events

    # Trim results
    filtered = filtered[:60]

    return JsonResponse({
        'center': {'lat': lat, 'lon': lon, 'radius_m': radius},
        'preferences': interests,
        'count': len(filtered),
        'events': filtered
    })


