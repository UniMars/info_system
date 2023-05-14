import datetime
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from datas.models import GovDoc, WeiboDoc, ToutiaoDoc

logger = logging.getLogger('django')


# Create your views here.
def home(request):
    logger.info('django project start successfully')
    return render(request, 'home.html', {'current': datetime.datetime.now()})


@cache_page(60 * 15)
def get_doc_sum(request):
    gov_count = GovDoc.objects.count()
    weibo_count = WeiboDoc.objects.count()
    toutiao_count = ToutiaoDoc.objects.count()
    return JsonResponse({'DocSum': gov_count + weibo_count + toutiao_count})
