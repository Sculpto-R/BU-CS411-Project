from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Profile, BOROUGH_CHOICES
from django.conf import settings
from django.core.exceptions import ValidationError
import datetime

PREDEFINED_KEYWORDS = [
    'rave', 'party', 'house concert', 'techno', 'drum & bass',
    'indie', 'open mic', 'comedy', 'art show'
]

class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password (again)', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'date_of_birth', 'borough', 'full_name')

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords don't match")
        return p2

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        # model validator will check age, but repeat here to give immediate form error
        if dob:
            today = datetime.date.today()
            years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if years < 18:
                raise ValidationError("You must be 18 or older to register.")
        return dob

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        # user inactive until email confirmed
        user.is_active = False
        if commit:
            user.save()
            Profile.objects.get_or_create(user=user)
        return user

class LoginEmailForm(AuthenticationForm):
    username = forms.EmailField(label='Email')

class ProfileForm(forms.ModelForm):
    # checkbox choices for predefined keywords
    predefined = forms.MultipleChoiceField(
        label='Choose from suggestions',
        choices=[(k, k) for k in PREDEFINED_KEYWORDS],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    custom = forms.CharField(
        label='Custom keywords (comma separated)',
        widget=forms.TextInput,
        required=False,
        help_text='e.g. "secret gig, vinyl night"'
    )

    class Meta:
        model = Profile
        fields = ('display_name', 'avatar')

    def __init__(self, *args, **kwargs):
        pref_initial = kwargs.pop('pref_initial', None)
        super().__init__(*args, **kwargs)
        if pref_initial is not None:
            # split into predefined & custom
            self.fields['predefined'].initial = [p for p in pref_initial if p in [c[0] for c in self.fields['predefined'].choices]]
            custom_list = [p for p in pref_initial if p not in [c[0] for c in self.fields['predefined'].choices]]
            self.fields['custom'].initial = ', '.join(custom_list)

    def clean(self):
        cleaned = super().clean()
        # no extra validation for now
        return cleaned

    def save(self, commit=True, user=None):
        profile = super().save(commit=False)
        predefined = self.cleaned_data.get('predefined') or []
        custom_raw = self.cleaned_data.get('custom') or ''
        custom_items = [c.strip() for c in custom_raw.split(',') if c.strip()]
        preferences = []
        # maintain order: predefined then custom
        preferences.extend(predefined)
        # dedupe while preserving order
        for item in custom_items:
            if item not in preferences:
                preferences.append(item)
        profile.preferences = preferences
        if commit:
            profile.save()
        return profile
