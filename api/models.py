from django.db import models


class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    location = models.CharField(max_length=255, blank=True)

    #start/end
    date_start = models.DateTimeField(null=True, blank=True)
    date_end = models.DateTimeField(null=True, blank=True)

    # price
    price_min = models.FloatField(null=True, blank=True)
    price_max = models.FloatField(null=True, blank=True)

    # age
    age_restriction = models.CharField(max_length=50, blank=True)

    #AI stuff
    ai_score = models.FloatField(null=True, blank=True)
    # IMPORTANT: JSONField, not TextField
    ai_tags = models.JSONField(blank=True, null=True, default=list)

    # map stuff
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Event {self.pk}"

