from django.db import models

# Create your models here.
class Event(models.Model):
    title = models.CharField(max_length = 200)
    description = models.TextField(blank = True)
    date_start = models.CharField(max_length = 32, blank = True, null = True)
    date_end = models.CharField(max_length = 32, blank = True, null = True)
    location = models.CharField(max_length = 120, blank = True, null = True)
    price_min = models.FloatField(blank = True, null = True)
    price_max = models.FloatField(blank = True, null = True)
    age_restriction = models.CharField(max_length = 16, blank = True, null = True)
    ai_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add = True)
    ai_tags = models.JSONField(default=list, blank=True, null=True)

