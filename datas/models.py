import uuid

from django.db import models


# Create your models here.

class GovAggr(models.Model):
    area = models.CharField(max_length=50)
    types = models.CharField(max_length=500)
    link = models.CharField(max_length=2000)
    title = models.CharField(max_length=500)
    content = models.CharField(max_length=10000)
    pub_date = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=50)
    level = models.CharField(max_length=50)
    is_split = models.BooleanField(default=False)

    class Meta:
        unique_together = ('area', 'title', 'pub_date')


class Sina(models.Model):
    pass


class KeyWord(models.Model):
    keyword = models.CharField(unique=True, max_length=50)


class GovAggrWordFreq(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    word = models.CharField(max_length=50)
    freq = models.IntegerField()
    record = models.ForeignKey(GovAggr, on_delete=models.CASCADE)
    # area = models.CharField(max_length=50)

    class Meta:
        unique_together = ('word', 'record_id')
