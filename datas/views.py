# -*- coding: utf-8 -*-
import logging
# import multiprocessing

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from .models import GovDoc, GovDocWordFreqAggr
from .tasks import gov_data_import, word_split

logger = logging.getLogger('django')


# Create your views here.
def index(response):
    # return
    return render(response, 'dataDemo.html')


def handle_task_request(request):
    task_type = request.GET.get('task_type')
    task_params = request.GET.get('task_params')
    logger.info(f"task_type:{task_type}, task_params:{task_params}")

    if task_type == 'gov_data_import':
        message = gov_data_import()
        code = 200 if message == "success" else 404
        result = {'code': code, 'message': message}
    elif task_type == 'word_split':
        message = word_split()
        code = 200 if message == "success" else 404
        result = {'code': code, 'message': message}
    else:
        result = {'code': 404, 'message': 'Invalid task type'}

    return JsonResponse(result)


@cache_page(7200)
def table_update(request):
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        # search_value = request.GET.get('search[value]', '')
        queryset = GovDoc.objects.all().order_by('-pub_date')[:1000]
        total_records = queryset.count()

        paginator = Paginator(queryset, length)
        page_number = (start // length) + 1
        data = [{'发布日期': obj.pub_date, '地区': obj.area, '类型': obj.types, '标题': obj.title, '来源': obj.source,
                 '级别': obj.level, }
                for obj in paginator.get_page(page_number)]
        response = {'draw': draw, 'recordsTotal': total_records, 'recordsFiltered': total_records, 'data': data}
        return JsonResponse(response)
    except Exception as e:
        data = {'update': False}
        logger.error(f"TABLE UPDATE ERROR:{e}")
        return JsonResponse(data, safe=False)


@cache_page(7200)
def wordcloud(request):
    logger.info('wordcloud start')
    aggregated_words = GovDocWordFreqAggr.objects.filter(area='TOTAL').order_by('-freq')[:1000]
    word_freq = [{'name': word.word, 'value': word.freq} for word in aggregated_words]
    # logger.info(f'wordfreq:{word_freq}')
    context = {'word_freq': word_freq}
    logger.info('wordcloud end')
    return JsonResponse(context)
