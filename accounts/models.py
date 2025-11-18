from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    date_of_birth = models.DateField(null=True, blank=True)
    age_verified = models.BooleanField(default=False)

    # Preferences
    presets = models.JSONField(default=list, blank=True)
    custom_preferences = models.JSONField(default=list, blank=True)

    # Profile fields
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    # Optional profile picture
    profile_picture = models.ImageField(upload_to="profile_pics/", null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# Auto-create Profile for each new User
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_profile_for_new_user(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
