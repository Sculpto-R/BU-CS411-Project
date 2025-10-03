from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import RegisterForm, LoginEmailForm, ProfileForm
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from .tokens import make_email_token, check_email_token
from .models import User, Profile
from django.template.loader import render_to_string
from django.http import HttpResponse

def home(request):
    # placeholder homepage - will hold the map in future
    user = request.user if request.user.is_authenticated else None
    prefs = user.profile.preferences if user and hasattr(user, 'profile') else []
    context = {'user': user, 'preferences': prefs}
    return render(request, 'accounts/home.html', context)

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_verification_email(request, user)
            messages.success(request, "Account created. Check your email for verification link.")
            return redirect('accounts:login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def send_verification_email(request, user):
    token = make_email_token(user.email)
    verify_url = request.build_absolute_uri(reverse('accounts:verify_email') + f'?token={token}')
    subject = 'Verify your email for EventsMap (London)'
    message = render_to_string('accounts/email/verification_email.txt', {
        'user': user,
        'verify_url': verify_url,
        'expiry_seconds': getattr(settings, 'EMAIL_VERIFICATION_EXPIRY', 3 * 24 * 3600)
    })
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    send_mail(subject, message, from_email, [user.email], fail_silently=False)

def verify_email(request):
    token = request.GET.get('token')
    email = check_email_token(token)
    if not email:
        return render(request, 'accounts/email/verification_failed.html')
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return render(request, 'accounts/email/verification_failed.html')
    user.is_active = True
    user.save()
    messages.success(request, "Email verified. You can now log in.")
    return redirect('accounts:login')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = LoginEmailForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_active:
                messages.error(request, "Account is inactive. Please verify your email.")
                return redirect('accounts:login')
            login(request, user)
            return redirect('home')
    else:
        form = LoginEmailForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('accounts:login')

from django.contrib.auth.decorators import login_required

@login_required
def profile_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        # pass initial pref so form shows them
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, "Profile updated.")
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=profile, pref_initial=profile.preferences)
    return render(request, 'accounts/profile.html', {'form': form, 'profile': profile})
