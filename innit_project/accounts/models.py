from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    date_of_birth = models.DateField(null=True, blank=True)
    age_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile({self.user.username})"

    def age(self):
        """Return integer years or None if DOB missing."""
        if not self.date_of_birth:
            return None
        today = timezone.localdate()
        dob = self.date_of_birth
        years = (
            today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        )
        return years
