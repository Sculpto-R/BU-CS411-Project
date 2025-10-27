from django.db import models
from django.contrib.auth.models import User
from datetime import date
from django.core.exceptions import ValidationError

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    date_of_birth = models.DateField(null=True, blank=True)
    age_verified = models.BooleanField(default=False)

    # Store preset selected preferences as list of strings
    presets = models.JSONField(default=list, blank=True)
    # Store custom preferences as list of strings
    custom_preferences = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile({self.user.username})"

    def is_adult(self):
        if not self.date_of_birth:
            return False
        today = date.today()
        age = today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
        return age >= 18

    def get_all_preferences(self):
        # Return combined list of presets + custom (preserve custom after presets)
        return list(self.presets) + list(self.custom_preferences)
