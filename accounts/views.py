import logging
from datetime import datetime

# User management
from django.conf import settings
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
from .services.scraper import fetch_events_for_preferences

from .forms import AccountForm, DOBForm, PreferencesForm, CustomPasswordChangeForm, ProfileEditForm
from .models import Profile

# Mapping API integration
import math
import requests
from bs4 import BeautifulSoup
from django.http import JsonResponse, HttpResponseBadRequest
from datetime import datetime, date
from django.views.decorators.http import require_GET

logger = logging.getLogger("accounts")

REG_SESSION_KEY = 'reg_data'

def normalize_preferences(profile):
    """
    Returns a consistent preference format for the frontend map.
    """
    if not profile:
        return {
            "presets": [],
            "custom": [],
        }

    return {
        "presets": profile.presets or [],
        "custom": profile.custom_preferences or [],
    }


def clear_reg_session(request):
    if REG_SESSION_KEY in request.session:
        del request.session[REG_SESSION_KEY]

def get_reg_data(request):
    return request.session.get(REG_SESSION_KEY, {})

def set_reg_data(request, data):
    request.session[REG_SESSION_KEY] = data
    request.session.modified = True

# -------------------------
# Landing / Home
# -------------------------

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'landing.html')

@login_required
def home_screen(request):
    """
    Main homepage with interactive map showing events.
    Pulls from the api_find_events endpoint asynchronously via JS.
    """
    profile = getattr(request.user, 'profile', None)
    prefs = normalize_preferences(profile)
    return render(request, 'accounts/home.html', {
    'profile': profile,
    'preferences': prefs,
    'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
})


# -------------------------
# Auth Views
# -------------------------

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
        logger.info("Logout requested for user %s via GET",
                    request.user.username if request.user.is_authenticated else "anonymous")
        return self.post(request, *args, **kwargs)

# -------------------------
# Registration Steps
# -------------------------

def reg_step1(request):
    set_reg_data(request, {})
    progress = 1
    return render(request, 'accounts/register_step1.html', {'progress': progress})

def reg_step2(request):
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
                'password': form.cleaned_data['password1'],
            }
            set_reg_data(request, reg_data)
            return redirect('accounts:register_step3')
    else:
        initial = reg_data.get('account', {})
        form = AccountForm(initial=initial)
    progress = 2
    return render(request, 'accounts/register_step2.html', {'form': form, 'progress': progress})

def reg_step3(request):
    if request.user.is_authenticated:
        return redirect('home')
    reg_data = get_reg_data(request)
    if request.method == 'POST':
        form = DOBForm(request.POST)
        if form.is_valid():
            reg_data['dob'] = str(form.cleaned_data['date_of_birth'])
            set_reg_data(request, reg_data)
            return redirect('accounts:register_step4')
    else:
        initial = {'date_of_birth': reg_data.get('dob')}
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
            prefs = reg_data.get('preferences')
            if not acct or not dob or not prefs:
                messages.error(request, "Registration data incomplete; please restart registration.")
                return redirect('accounts:register_step1')

            from django.contrib.auth.models import User
            if User.objects.filter(username__iexact=acct['username']).exists():
                messages.error(request, "A user with that username already exists.")
                return redirect('accounts:register_step2')

            from datetime import datetime
            dob_date = datetime.fromisoformat(dob).date()

            user = User.objects.create_user(
                username=acct['username'],
                email=acct['email'],
                password=acct['password'],
                first_name=acct['first_name'],
                last_name=acct['last_name'],
            )

            profile = Profile.objects.get(user=user)
            profile.date_of_birth = dob_date
            profile.age_verified = True
            profile.presets = prefs['presets']
            profile.custom_preferences = prefs['custom']
            profile.save()

            login(request, user)
            clear_reg_session(request)
            return redirect('accounts:welcome')
    else:
        initial = reg_data.get('preferences', {})
        initial['custom_preferences'] = ', '.join(initial.get('custom', []))
        form = PreferencesForm(initial=initial)
    return render(request, 'accounts/register_step4.html',
                  {'form': form, 'progress': 4})

@login_required
def welcome(request):
    profile = getattr(request.user, 'profile', None)
    return render(request, 'accounts/welcome.html', {'profile': profile})

# -------------------------
# Profile & Editing
# -------------------------

@login_required
def profile(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    if request.method == 'POST':
        if 'save_profile' in request.POST:
            form = ProfileEditForm(request.POST, instance=profile, user=user)
            pwd_form = CustomPasswordChangeForm(user)
            if form.is_valid():
                form.save(user=user)
                messages.success(request, "Profile updated successfully.")
                return redirect('accounts:profile')

        elif 'change_password' in request.POST:
            form = ProfileEditForm(user=user, instance=profile)
            pwd_form = CustomPasswordChangeForm(user, request.POST)
            if pwd_form.is_valid():
                pwd_form.save()
                update_sess_
