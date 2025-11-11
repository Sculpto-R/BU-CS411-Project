from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "location", "date_start", "ai_score", "show_ai_tags")

    def show_ai_tags(self, obj):
        return ", ".join(obj.ai_tags or [])
    show_ai_tags.short_description = "AI Tags"


