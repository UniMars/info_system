from django.db import models


# Create your models here.

class DataAggr(models.Model):
    area = models.CharField(max_length=50)
    types = models.CharField(max_length=50)
    link = models.CharField(max_length=2000)
    title = models.CharField(max_length=500)
    content = models.CharField(max_length=50000)
    pub_date = models.DateTimeField(null=True, blank=True)
    department = models.CharField(max_length=50)
    level = models.CharField(max_length=50)
    cate = models.CharField(max_length=50)
