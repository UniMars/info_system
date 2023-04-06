from django.contrib import admin
from .models import GovDoc, KeyWord, GovDocWordFreq

# Register your models here.

admin.site.register(GovDoc)
admin.site.register(GovDocWordFreq)
