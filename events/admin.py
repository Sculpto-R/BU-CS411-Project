from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    # ONLY fields that definitely exist on events.Event
    list_display = ("id", "title")

