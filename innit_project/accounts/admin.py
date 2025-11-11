from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "date_of_birth", "age_verified", "created_at")
    search_fields = ("user__username", "user__email")
