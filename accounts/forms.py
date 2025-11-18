from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from .models import Profile

# ------------------------------------------
# Account Creation (Step 2)
# ------------------------------------------

class AccountForm(forms.Form):
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        
        if cleaned.get('password1') != cleaned.get('password2'):
            raise forms.ValidationError("Passwords do not match.")

        if User.objects.filter(username__iexact=cleaned.get('username')).exists():
            raise forms.ValidationError("That username is already in use.")
        
        return cleaned

# ------------------------------------------
# DOB Collection (Step 3)
# ------------------------------------------

class DOBForm(forms.Form):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

# ------------------------------------------
# Preferences Form (Step 4 + Editing)
# ------------------------------------------

class PreferencesForm(forms.Form):
    presets = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=[
            ('party', 'Parties'),
            ('club', 'Clubbing'),
            ('concert', 'Concerts'),
            ('festival', 'Festivals'),
            ('exhibition', 'Exhibitions'),
            ('meetup', 'Meetups'),
            ('other', 'Other'),
        ]
    )

    custom_preferences = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Comma-separated list...'})
    )

    def clean_custom_list(self):
        raw = self.cleaned_data.get('custom_preferences', '')
        return [i.strip() for i in raw.split(',') if i.strip()]

# ------------------------------------------
# Profile Editing
# ------------------------------------------

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'bio']

    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    bio = forms.CharField(required=False, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True, user=None):
        profile = super().save(commit=False)
        if user:
            profile.user = user
        if commit:
            profile.save()
        return profile

# ------------------------------------------
# Password Change
# ------------------------------------------

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput)
    new_password1 = forms.CharField(widget=forms.PasswordInput)
    new_password2 = forms.CharField(widget=forms.PasswordInput)

