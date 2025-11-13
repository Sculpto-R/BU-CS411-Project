from django.db import models

class Event(models.Model):
    title = models.CharField(...)
    description = models.TextField(...)
    city = models.CharField(...)
    address = models.CharField(...)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    ai_score = models.FloatField(blank=True, null=True)
    ai_tags = models.JSONField(blank=True, null=True)
