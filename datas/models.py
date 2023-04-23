import uuid

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver


# Create your models here.
class TestModel(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    name = models.CharField(max_length=50, default='test_name')
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


# 搜索关键词
class KeyWord(models.Model):
    keyword = models.CharField(unique=True, max_length=50)

    def __str__(self):
        return self.keyword


# 数据来源
class DataType(models.Model):
    id = models.BigIntegerField(primary_key=True, editable=False)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


# 地区关键词
class Area(models.Model):
    name = models.CharField(unique=True, max_length=50)
    level=models.IntegerField(default=0)

    def __str__(self):
        return self.name


class GovDoc(models.Model):
    area = models.CharField(max_length=50, blank=True)
    types = models.CharField(max_length=500, blank=True)
    link = models.TextField(blank=True)
    title = models.CharField(max_length=500, blank=True)
    content = models.TextField(blank=True)
    pub_date = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=50, blank=True)
    level = models.CharField(max_length=50, blank=True)
    is_split = models.BooleanField(default=False, blank=True)

    class Meta:
        unique_together = ('area', 'title', 'pub_date')


class GovDocWordFreq(models.Model):
    id = models.BigIntegerField(primary_key=True, editable=False)
    word = models.CharField(max_length=500)
    freq = models.IntegerField(default=0)
    record = models.ForeignKey(GovDoc, on_delete=models.CASCADE)
    pub_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('word', 'record_id')


class GovDocWordFreqAggr(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False, verbose_name="ID")
    word = models.CharField(max_length=500)
    freq = models.IntegerField(default=0)
    area = models.CharField(max_length=50, default='TOTAL')

    class Meta:
        unique_together = ('word', 'area')


class ToutiaoDoc(models.Model):
    area = models.CharField(max_length=50, blank=True)
    search_keyword = models.CharField(max_length=50, blank=True)
    link = models.TextField(blank=True)
    title = models.CharField(max_length=500, blank=True)
    pub_date = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=50, blank=True)
    context = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    is_split = models.BooleanField(default=False, blank=True)

    class Meta:
        unique_together = ('area', 'title', 'pub_date')


class ToutiaoDocWordFreq(models.Model):
    id = models.BigIntegerField(primary_key=True, editable=False)
    word = models.CharField(max_length=500)
    freq = models.IntegerField(default=0)
    record = models.ForeignKey(ToutiaoDoc, on_delete=models.CASCADE)
    pub_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('word', 'record_id')


class ToutiaoDocWordFreqAggr(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False, verbose_name="ID")
    word = models.CharField(max_length=500)
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
