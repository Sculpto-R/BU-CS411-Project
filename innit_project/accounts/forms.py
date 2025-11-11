from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from datetime import date


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True, help_text="Required. We'll send notifications here."
    )
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="You must be 18 or older to register.",
    )

    class Meta:
        model = User
        fields = ["username", "email", "date_of_birth", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if not dob:
            raise forms.ValidationError("Please enter your date of birth.")
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise forms.ValidationError(
                "You must be at least 18 years old to register."
            )
        return dob


class AgeVerificationForm(forms.Form):
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if not dob:
            raise forms.ValidationError("Please enter your date of birth.")
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise forms.ValidationError("You must be at least 18 years old.")
        return dob
