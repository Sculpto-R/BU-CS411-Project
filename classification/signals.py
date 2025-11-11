from django.db.models.signals import post_save
from django.dispatch import receiver
from ingestion.models import RawPost
from classification.services import build_event_candidate

@receiver(post_save, sender=RawPost)

def make_candidate_on_rawpost_save(sender, instance, created, **kwargs):
    if created and (instance.caption or "").strip() != "":
        try:
            build_event_candidate(instance.id)
        except Exception:
            pass
    