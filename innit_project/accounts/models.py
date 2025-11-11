from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField  # Not necessary; we'll use JSONField below
from django.db.models import JSONField
from datetime import date

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    date_of_birth = models.DateField(null=True, blank=True)
    age_verified = models.BooleanField(default=False)

    # store presets and custom as JSON arrays (list of strings)
    presets = JSONField(default=list, blank=True)              # e.g. ["party", "concert"]
    custom_preferences = JSONField(default=list, blank=True)   # e.g. ["indie", "open-mic"]

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

    def export_preferences(self):
        """
        Return a normalized list of lowercase tokens representing preferences,
        suitable for mapping APIs / scrapers.
        Example output: ['party','concert','indie']
        """
        prefs = []
        # unify presets and custom_preferences which are lists
        if isinstance(self.presets, (list, tuple)):
            prefs.extend([str(p).strip().lower() for p in self.presets if p])
        if isinstance(self.custom_preferences, (list, tuple)):
            prefs.extend([str(p).strip().lower() for p in self.custom_preferences if p])
        # dedupe preserving order
        seen = set()
        out = []
        for p in prefs:
            if p not in seen:
                seen.add(p)
                out.append(p)
        return out


class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferred_categories = models.JSONField(default=list)
    preferred_areas = models.JSONField(default=list)
    min_price = models.FloatField(blank=True, null=True)
    max_price = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"Preferences for {self.user.username}"

    # e.g: UserPreference.objects.filter(preferred_areas__contains=['Shoreditch'])
    # Scraped events can be filtered per-user and then pinned on a future map.
