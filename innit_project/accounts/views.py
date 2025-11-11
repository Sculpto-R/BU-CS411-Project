from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings

from .forms import RegistrationForm, AgeVerificationForm
from .models import Profile


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


def register(request):
    """Register a new user and set DOB + age_verified=True (since we validate DOB)."""
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data["email"]
            user.save()

            # profile is auto-created via signal; update it
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.date_of_birth = form.cleaned_data["date_of_birth"]
            profile.age_verified = True
            profile.save()

            # Send welcome email (console backend in dev)
            subject = "Welcome to iNNiT"
            plain_message = (
                f"Hi {user.username},\n\n"
                "Thanks for registering at iNNiT. We're excited to have you on board!"
            )
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            # log user in
            login(request, user)
            messages.success(request, "Registration successful. Welcome!")
            return redirect("accounts:profile")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    profile = getattr(request.user, "profile", None)
    return render(request, "accounts/profile.html", {"profile": profile})


@login_required
def verify_age(request):
    """A page allowing existing users who didn't verify to provide DOB and become age_verified."""
    profile = getattr(request.user, "profile", None)
    if request.method == "POST":
        form = AgeVerificationForm(request.POST)
        if form.is_valid():
            dob = form.cleaned_data["date_of_birth"]
            profile.date_of_birth = dob
            profile.age_verified = True
            profile.save()
            messages.success(request, "Thank you — your age has been verified.")
            return redirect("accounts:profile")
    else:
        initial = {}
        if profile and profile.date_of_birth:
            initial["date_of_birth"] = profile.date_of_birth
        form = AgeVerificationForm(initial=initial)
    return render(request, "accounts/verify_age.html", {"form": form})
