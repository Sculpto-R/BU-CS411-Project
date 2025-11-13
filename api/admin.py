from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "location",
        "date_start",
        "date_end",
        "price_min",
        "price_max",
        "ai_score",
        "ai_tags",
        "latitude",
        "longitude",
    )
    list_filter = ("location",)
    search_fields = ("title", "location", "ai_tags")

