from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings

from .forms import AccountForm, DOBForm, PreferencesForm, CustomPasswordChangeForm, ProfileEditForm
from .models import Profile

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
def home_screen(request):
    return render(request, 'home.html')


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('landing')
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


def reg_step1(request):
    """
    Step 1: Intro page. No form — starts the session data.
    """
    # initialize session store
    set_reg_data(request, {})
    progress = 1
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
            return redirect('accounts:register_step3')
    else:
        # prefill from session if present
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
            return redirect('accounts:register_step4')
    else:
        initial = {}
        if 'dob' in reg_data:
            initial['date_of_birth'] = reg_data['dob']
        form = DOBForm(initial=initial)
    progress = 3
    return render(request, 'accounts/register_step3.html', {'form': form, 'progress': progress})


def reg_step4(request):
    """
    Step 4: Preferences (preset multi-select + up to 3 custom)
    """
    if request.user.is_authenticated:
        return redirect('home')
    reg_data = get_reg_data(request)
    if request.method == 'POST':
        form = PreferencesForm(request.POST)
        if form.is_valid():
            # Save presets and custom_list into session
            reg_data['preferences'] = {
                'presets': form.cleaned_data['presets'],
                'custom': form.cleaned_data['custom_list'],
            }
            set_reg_data(request, reg_data)

            # All steps complete
            acct = reg_data.get('account')
            dob = reg_data.get('dob')
            prefs = reg_data.get('preferences', {})
            if not acct or not dob or not prefs:
                messages.error(request, "Registration data incomplete; please restart registration.")
                return redirect('accounts:register_step1')

            # Create user
            from django.contrib.auth.models import User
            username = acct['username']
            # ensure username unique (should be validated by AccountForm)
            if User.objects.filter(username__iexact=username).exists():
                messages.error(request, "A user with that username already exists. Please choose another.")
                return redirect('accounts:register_step2')

            user = User.objects.create_user(
                username=username,
                email=acct['email'],
                password=acct['password'],
                first_name=acct.get('first_name', ''),
                last_name=acct.get('last_name', ''),
            )

            # Create Profile (signals may auto-create but we ensure it)
            profile, _ = Profile.objects.get_or_create(user=user)
            from datetime import datetime
            profile.date_of_birth = datetime.strptime(dob, "%Y-%m-%d").date()
            profile.age_verified = True
            profile.presets = prefs.get('presets', [])
            profile.custom_preferences = prefs.get('custom', [])
            profile.save()

            # Send welcome email (console backend by default in dev)
            subject = "Welcome to iNNiT"
            body = f"Hi {user.first_name or user.username},\n\nWelcome to iNNiT! Your account is ready."
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)

            login(request, user)

            clear_reg_session(request)

            return redirect('accounts:welcome')
    else:
        initial = {}
        if 'preferences' in reg_data:
            prefs = reg_data['preferences']
            initial['presets'] = prefs.get('presets', [])
            # join custom list to string
            initial['custom_preferences'] = ', '.join(prefs.get('custom', []))
        form = PreferencesForm(initial=initial)
    progress = 4
    return render(request, 'accounts/register_step4.html', {'form': form, 'progress': progress})


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
                return redirect('accounts:profile')

        elif 'change_password' in request.POST:
            form = ProfileEditForm(user=user, instance=profile)
            pwd_form = CustomPasswordChangeForm(user, request.POST)
            if pwd_form.is_valid():
                pwd_form.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed successfully.")
                return redirect('accounts:profile')
    else:
        form = ProfileEditForm(user=user, instance=profile)
        pwd_form = CustomPasswordChangeForm(user)

    return render(
        request,
        'accounts/profile.html',
        {'form': form, 'pwd_form': pwd_form}
    )
