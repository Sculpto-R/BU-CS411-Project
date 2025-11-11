from django.contrib import admin
from .models import RawPost


# Register your models here.
@admin.register(RawPost)
class RawPostAdmin(admin.ModelAdmin):
    list_display = ("id", "source", "created_at", "processed_at")
    search_fields = ("caption", "source")
