import uuid

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver


# Create your models here.

class GovDoc(models.Model):
    area = models.CharField(max_length=50)
    types = models.CharField(max_length=500)
    link = models.TextField()
    title = models.CharField(max_length=500)
    content = models.TextField()
    pub_date = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=50)
    level = models.CharField(max_length=50)
    is_split = models.BooleanField(default=False)

    class Meta:
        unique_together = ('area', 'title', 'pub_date')


class KeyWord(models.Model):
    keyword = models.CharField(unique=True, max_length=50)


class GovDocWordFreq(models.Model):
    id = models.BigIntegerField(primary_key=True, editable=False)
    word = models.CharField(max_length=50)
    freq = models.IntegerField(default=0)
    record = models.ForeignKey(GovDoc, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('word', 'record_id')


class GovDocWordFreqAggr(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    word = models.CharField(max_length=50)
    freq = models.IntegerField(default=0)
    area = models.CharField(max_length=50, default='TOTAL')

    class Meta:
        unique_together = ('word', 'area')


class TestModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    name = models.CharField(max_length=50)
    age = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        print('save!!!')
        if not self.id:
            self.id = uuid.uuid4()
        if not self.age:
            self.age = 114514
        super().save(*args, **kwargs)


@receiver(pre_save, sender=TestModel)
def set_id(sender, instance, **kwargs):
    print('pre save')
    if not instance.id:
        # set id to a positive integer
        instance.id = uuid.uuid4()
