from django.db import models

class Map(models.Model):
    name = models.CharField(max_length=100)

class Variable(models.Model): # Every map will have multiple variables, this is where certain types will defined/typecast.
    map = models.ForeignKey(Map, related_name='variables', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    data_type = models.CharField(max_length=50, choices=[
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('string', 'String'),
        ('boolean', 'Boolean'),
    ])
    value = models.TextField()

    def cast_value(self):
        if self.data_type == 'integer':
            return int(self.value)
        elif self.data_type == 'float':
            return float(self.value)
        elif self.data_type == 'boolean':
            return self.value.lower() == 'true'
        return self.value
