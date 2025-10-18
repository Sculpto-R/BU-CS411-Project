from django.contrib import admin
from .models import EventCandidate

#When creating a class, Djano creates a web interface where one can 
#add, edit, delete and search RawPost rows

#admin allows for site management 


# Register your models here.
@admin.register(EventCandidate)

class EventCandidateModule(admin.ModelAdmin):
    list_display = ("id", "raw_post", "score", "needs_review", "created_at")
    list_filter = ("needs_review",)
    search_fields = ("raw_post_caption",)


