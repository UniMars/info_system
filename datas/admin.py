from django.contrib import admin
from .models import GovDoc, KeyWord, GovDocWordFreq, GovDocWordFreqAggr, DataType

# Register your models here.

admin.site.register(GovDoc)
admin.site.register(GovDocWordFreq)
admin.site.register(GovDocWordFreqAggr)
admin.site.register(KeyWord)
admin.site.register(DataType)
