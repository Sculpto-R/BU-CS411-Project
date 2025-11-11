from django.db import models
from ingestion.models import RawPost

# Create your models here.


class EventCandidate(models.Model):
    raw_post = models.ForeignKey(RawPost, on_delete=models.CASCADE)
    extracted_json = models.JSONField()
    score = models.FloatField(default=0)
    needs_review = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f" Event Candidate from {self.raw_post.source} ({self.score:.2f})"
