from django.contrib import admin
from .models import EventCandidate
from .services import promote_candidate_to_event

#When creating a class, Djano creates a web interface where one can 
#add, edit, delete and search RawPost rows

#admin allows for site management 


# Register your models here.
@admin.register(EventCandidate)

class EventCandidateModule(admin.ModelAdmin):
    list_display = ("id", "raw_post", "score", "needs_review", "created_at")
    list_filter = ("needs_review",)
    search_fields = ("raw_post_caption",)
    actions = ["promote_to_event"]

    def promote_to_event(self, request, queryset):
        created = 0
        for cand in queryset:
            try:
                promote_candidate_to_event(cand.id)
            except Exception:
                pass
        
        self.message_user(request, f"Promoted {created} candidate(s) to Event.")
    promote_to_event.short_description = "Promote to Event"

