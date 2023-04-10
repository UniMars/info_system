# -*- coding: utf-8 -*-
import logging

from django.core.cache import cache
# import multiprocessing

from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseNotFound
from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import cache_page

from .models import GovDoc, GovDocWordFreqAggr, DataType
from .tasks import gov_data_import, word_split

logger = logging.getLogger('django')


# Create your views here.
def index(response, data_id):
    try:
        data_type = get_object_or_404(DataType, pk=data_id)
        context = {"data_type": data_type}
        logger.info(f"Data type: {data_type}")
    except Exception as e:
        logger.error(e)
        return render(response, '404.html', status=404)
    else:
        return render(response, 'dataDemo.html', context)


def handle_task_request(request, data_id):
    if data_id != 1:
        return
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
def table_update(request, data_id):
    data = {'update': False}
    if data_id == 1:
        order_column_dict = {
            '0': "pub_date",
            '1': "area",
            '2': "types",
            '3': "source",
            '4': "level",
            '5': "title",
        }
        try:
            draw = int(request.GET.get('draw', 1))
            start = int(request.GET.get('start', 0))
            length = int(request.GET.get('length', 10))
            order_column = request.GET.get('order[0][column]')
            order_direction = request.GET.get('order[0][dir]')
            order_column_str = order_column_dict[order_column]
            # search_value = request.GET.get('search[value]', '')
            queryset = cache.get('gov_doc_total')
            if not queryset:
                queryset = GovDoc.objects.all().order_by('-pub_date')[:1000]
                cache.set('gov_doc_total', queryset, 7200)
            sorted_queryset = sorted(queryset, key=lambda x: getattr(x, order_column_str),
                                     reverse=True if order_direction == 'desc' else False)

            total_records = len(sorted_queryset)
            page_number = (start // length) + 1
            data = [{'发布日期': obj.pub_date,
                     '地区': obj.area,
                     '类型': obj.types,
                     '标题': obj.title,
                     '来源': obj.source,
                     '级别': obj.level, }
                    for obj in sorted_queryset[(page_number - 1) * length:page_number * length]]
            response = {'draw': draw, 'recordsTotal': total_records, 'recordsFiltered': total_records, 'data': data}
            return JsonResponse(response)
        except Exception as e:
            logger.error(f"TABLE UPDATE ERROR:{e}")
            return JsonResponse(data, safe=False)
    elif data_id == 2:
        return JsonResponse(data, safe=False)
    elif data_id == 3:
        return JsonResponse(data, safe=False)
    else:
        logger.error(f"TABLE UPDATE ERROR:")
        return JsonResponse(data, safe=False)


@cache_page(7200)
def wordcloud(request, data_id):
    if data_id != 1:
        return JsonResponse({'word_freq': [{'name': '@TEST@', 'value': 1}]})
    logger.info('wordcloud start')
    aggregated_words = GovDocWordFreqAggr.objects.filter(area='TOTAL').order_by('-freq')[:1000]
    word_freq = [{'name': word.word, 'value': word.freq} for word in aggregated_words]
    context = {'word_freq': word_freq}
    logger.info('wordcloud end')
    return JsonResponse(context)
