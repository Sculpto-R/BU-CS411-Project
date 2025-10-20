# Last change: 10.20.25
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


def landing_page(request):
    """Public landing page for guests."""
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'landing.html')

@login_required
def home_screen(request):
    """Main home screen for logged-in users."""
    return render(request, 'home.html')


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True  # don't let logged-in users revisit login
    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)

class CustomLogoutView(LogoutView):
    """Logout view that accepts GET (for simplicity) and redirects to landing."""
    next_page = reverse_lazy('landing')

    def get(self, request, *args, **kwargs):
        # Handle GET logout as POST for smoother UX
        return self.post(request, *args, **kwargs)


def register(request):
    """User registration with age check + email notification."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()

            # profile is auto-created via signal
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.date_of_birth = form.cleaned_data['date_of_birth']
            profile.age_verified = True
            profile.save()

            # Send welcome email
            subject = "Welcome to iNNiT"
            body = f"Hi {user.username},\n\nWelcome to iNNiT!"
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])

            login(request, user)
            messages.success(request, "Registration successful. Welcome aboard!")
            return redirect('home')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    profile = getattr(request.user, 'profile', None)
    return render(request, 'accounts/profile.html', {'profile': profile})


@login_required
def verify_age(request):
    """Existing user can verify age manually if missing."""
    profile = getattr(request.user, 'profile', None)
    if request.method == 'POST':
        form = AgeVerificationForm(request.POST)
        if form.is_valid():
            dob = form.cleaned_data['date_of_birth']
            profile.date_of_birth = dob
            profile.age_verified = True
            profile.save()
            messages.success(request, "Your age has been verified.")
            return redirect('accounts:profile')
    else:
        form = AgeVerificationForm(initial={'date_of_birth': profile.date_of_birth} if profile.date_of_birth else None)
    return render(request, 'accounts/verify_age.html', {'form': form})
