import uuid

from django.db import models


# Create your models here.

class GovDoc(models.Model):
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


class GovDocWordFreq(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    word = models.CharField(max_length=50)
    freq = models.IntegerField(default=0)
    record = models.ForeignKey(GovDoc, on_delete=models.CASCADE)

    # area = models.CharField(max_length=50)

    class Meta:
        unique_together = ('word', 'record_id')


class GovDocWordFreqAggr(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    word = models.CharField(max_length=50)
    freq = models.IntegerField(default=0)
    area = models.CharField(max_length=50, default='TOTAL')

    class Meta:
        unique_together = ('word', 'area')

class data_province(models.Model):
    time=models.DateTimeField(null=True, blank=True)
    month =models.DateTimeField(null=True, blank=True)
    mblogurl=models.CharField(max_length=2000)
    mid=models.IntegerField(max_length=100)
    user_id =models.CharField(max_length=100)
    user_name =models.CharField(max_length=100)
    source=models.CharField(max_length=100)
    user_gender=models.CharField(max_length=10)
    user_statuses_count=models.IntegerField(max_length=100)
    user_followers_count=models.CharField(max_length=100)
    user_follow_count =models.CharField(max_length=100)
    user_verified =models.BooleanField()
    user_verified_type =models.IntegerField(max_length=10)
    user_verified_reason =models.CharField(max_length=1000)
    user_urank =models.IntegerField(max_length=50)
    location =models.CharField(max_length=1000)
    content =models.CharField(max_length=20000)
    length =models.IntegerField(max_length=100)
    is_splmt =models.IntegerField(max_length=100)
    splmt_type =models.CharField(max_length=100)
    splmt_title =models.CharField(max_length=500)
    splmt_url =models.CharField(max_length=1000)
    urls_num =models.IntegerField(max_length=50)
    reposts_count =models.IntegerField(max_length=50)
    comments_count =models.IntegerField(max_length=50)
    attitudes_count =models.IntegerField(max_length=50)
    pic_num =models.IntegerField(max_length=50)
