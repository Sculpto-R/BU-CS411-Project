from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.conf import settings
import datetime
from django.contrib.postgres.fields import ArrayField
try:
    # Django 3.1+ has JSONField in core
    from django.db.models import JSONField
except:
    from django.contrib.postgres.fields import JSONField

def validate_age_18_plus(dob):
    if dob is None:
        raise ValidationError("Date of birth is required.")
    today = timezone.localdate()
    years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if years < 18:
        raise ValidationError("You must be 18 or older to register.")

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', False)  # require email verification
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)  # superuser active by default

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)

BOROUGH_CHOICES = [
    ('Camden', 'Camden'),
    ('Greenwich', 'Greenwich'),
    ('Hackney', 'Hackney'),
    ('Hammersmith & Fulham', 'Hammersmith & Fulham'),
    ('Islington', 'Islington'),
    ('Kensington & Chelsea', 'Kensington & Chelsea'),
    ('Lambeth', 'Lambeth'),
    ('Lewisham', 'Lewisham'),
    ('Southwark', 'Southwark'),
    ('Tower Hamlets', 'Tower Hamlets'),
    ('Wandsworth', 'Wandsworth'),
    ('Westminster', 'Westminster'),
    # ... add other boroughs as needed
]

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150, blank=True)
    date_of_birth = models.DateField(validators=[validate_age_18_plus])
    borough = models.CharField(max_length=50, choices=BOROUGH_CHOICES, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)  # activated after email verify
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

def user_profile_picture_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'profiles/{instance.user.id}/avatar.{ext}'

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to=user_profile_picture_path, blank=True, null=True, validators=[FileExtensionValidator(['jpg','jpeg','png'])])
    # preferences stored as list of strings (keywords). Use JSONField for portability.
    preferences = JSONField(default=list, blank=True)
    # created/updated
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile for {self.user.email}'
