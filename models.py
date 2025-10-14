from django.db import models
#imports Django's model system, which lets us 
# define database tables as Python classes
#Using ORM (Object Relational Mapper) to define database tables as Python classes

# Create your models here.

#In Django, each class in models.oy is one database table 

#This is where messy social media posts will be stored 
# before they are cleaned with the AI filter

#Each row in database table equals one posted ingested

class RawPost(models.Model):
    source = models.CharField(max_length = 50) #tells us if the raw post came from instagram or tiktok
    caption = models.TextField() #caption from the raw post
    raw_json = models.JSONField(null = True, blank = True) #stores raw post as JSON 
    created_at = models.DateTimeField(auto_now_add = True) #records when row was created
    processed_at = models.DateTimeField(null = True, blank = True) #records when classifier finished processing post

    def __str__(self):
        
        return f"{self.source}: {self.caption[:30]}..."
    
