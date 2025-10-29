from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from datetime import date
from .models import Profile


# Preset list — change/add as needed
PRESET_PREFERENCES = [
    ('party', 'Party'),
    ('club', 'Club'),
    ('concert', 'Concert'),
    ('festival', 'Festival'),
    ('exhibition', 'Exhibition'),
    ('meetup', 'Meetup'),
    ('other', 'Other'),
]

# Step 2: account details
class AccountForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


# Step 3: DOB
class DOBForm(forms.Form):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="⚠️ This service is for users 18 and older",
        required=True
    )

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if not dob:
            raise forms.ValidationError("Please enter your date of birth.")
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise forms.ValidationError("You must be at least 18 years old to register.")
        return dob


# Step 4: preferences
class PreferencesForm(forms.Form):
    presets = forms.MultipleChoiceField(
        choices=PRESET_PREFERENCES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Pick one or more preset preferences."
    )

    # Accept comma-separated custom preferences as a single field
    # > (there's a BUG when EDITING preferences in the profile view that continuously adds brackets '[ ]' to the end of the user's input per save)
    custom_preferences = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Add custom preferences separated by commas (max 3)'}),
        help_text="Add up to 3 custom preferences (comma-separated)."
    )

    def clean(self):
        cleaned = super().clean()
        presets = cleaned.get('presets') or []
        custom_raw = cleaned.get('custom_preferences') or ''
        # Parse custom preferences into clean list
        custom_list = []
        if custom_raw.strip():
            # Split on commas and strip whitespace; ignore empty items
            items = [p.strip() for p in custom_raw.split(',') if p.strip()]
            # remove duplicates preserving order
            seen = set()
            for it in items:
                lowered = it.lower()
                if lowered not in seen:
                    seen.add(lowered)
                    custom_list.append(it)
        # validate max 3
        if len(custom_list) > 3:
            raise forms.ValidationError("Please limit custom preferences to at most 3 items.")
        # ensure at least one overall preference
        if not presets and not custom_list:
            raise forms.ValidationError("Please select at least one preference (preset or custom).")
        cleaned['custom_list'] = custom_list
        cleaned['presets'] = presets
        return cleaned

class ProfileEditForm(forms.ModelForm):
    """Form to edit user's profile info and preferences."""
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Must be 18 or older."
    )
    presets = forms.MultipleChoiceField(
        choices=[
            ('party', 'Party'),
            ('club', 'Club'),
            ('concert', 'Concert'),
            ('festival', 'Festival'),
            ('exhibition', 'Exhibition'),
            ('meetup', 'Meetup'),
            ('other', 'Other'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    custom_preferences = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Comma-separated custom preferences (max 3)'}),
        help_text="Add up to 3 custom preferences."
    )

    class Meta:
        model = Profile
        fields = ['date_of_birth', 'presets', 'custom_preferences']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

            profile = getattr(user, 'profile', None)
            if profile:
                self.fields['presets'].initial = profile.presets or []
                # Safely handle any stored format of custom_preferences
                raw_custom = profile.custom_preferences
                if isinstance(raw_custom, list):
                    self.fields['custom_preferences'].initial = ', '.join(raw_custom)
                elif isinstance(raw_custom, str):
                    # clean stringified list like "['a','b']" or '["a", "b"]'
                    cleaned = raw_custom.strip("[]").replace("'", "").replace('"', '')
                    self.fields['custom_preferences'].initial = ', '.join(
                        [p.strip() for p in cleaned.split(',') if p.strip()]
                    )
                else:
                    self.fields['custom_preferences'].initial = ''

    def clean_date_of_birth(self):
        from datetime import date
        dob = self.cleaned_data.get('date_of_birth')
        if not dob:
            raise forms.ValidationError("Please enter your date of birth.")
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise forms.ValidationError("You must be at least 18 years old.")
        return dob

    def clean_custom_preferences(self):
        raw = self.cleaned_data.get('custom_preferences', '')
        if not raw:
            return []

        # Remove stray brackets or quotes from stored values
        raw = raw.strip("[]").replace("'", "").replace('"', '')
        prefs = [p.strip() for p in raw.split(',') if p.strip()]
        prefs = list(dict.fromkeys(prefs))  # remove duplicates, preserve order

        if len(prefs) > 3:
            raise forms.ValidationError("Please limit to 3 custom preferences.")
        return prefs

    def save(self, user=None, commit=True):
        profile = super().save(commit=False)

        if user:
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            if commit:
                user.save()

        profile.presets = self.cleaned_data.get('presets', [])
        profile.custom_preferences = self.cleaned_data.get('custom_preferences', [])
        if commit:
            profile.save()
        return profile


class CustomPasswordChangeForm(PasswordChangeForm):
    """Simple subclass to customize template display."""
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Current password'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'New password'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm new password'}))
