# -*- coding: utf-8 -*-
import datetime
import json
import logging
import os

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from .apps import file_upload_queue, file_upload_start_event
from .models import GovDoc, GovDocWordFreqAggr, DataType, WordHotness, WeiboDoc, ToutiaoDoc, ToutiaoDocWordFreqAggr
from .tasks import gov_data_import, word_split, toutiao_data_import, test_celery_task
from .utils.utils import push_queue

# import multiprocessing

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
        return render(response, 'datas/dataDemo.html', context)


def handle_task_request(request, data_id):
    if data_id == 2:
        return
    task_type = request.GET.get('task_type')
    task_params_str = request.GET.get('task_params')
    task_params = json.loads(task_params_str)
    logger.info(f"task_type:{task_type}, task_params:{task_params}")

    if task_type == 'spider':
        # message = gov_data_import()
        message = "unable to start"
        code = 200 if message == "success" else 404
        result = {'code': code, 'message': message}
    elif task_type == 'word_split':
        logger.info('word_split start')
        data_type = task_params['data_type']
        # logger.info(ToutiaoDocWordFreq)
        message = word_split(data_type)
        code = 200 if message == "success" else 404
        result = {'code': code, 'message': message}
    else:
        result = {'code': 404, 'message': 'Invalid task type'}

    return JsonResponse(result)


@csrf_exempt
def upload_file(request, data_id):
    if request.method == 'POST':
        uploaded_file = request.FILES['uploadFile']
        file_name = uploaded_file.name

        # 保存文件到服务器
        file_dir = os.path.join(settings.BASE_DIR, 'DATA', str(data_id))
        file_path = os.path.join(file_dir, file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        logger.info(f"File {file_name} saved to {file_path}")
        # logger.info(data_id)

        # 返回 JSON 响应
        logger.info("upload finish")
        return JsonResponse({'status': 'success', 'filename': file_name})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@cache_page(72000)
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
        # cache.clear()
        queryset = cache.get('gov_doc_total')
        doc = GovDoc
        cache_key = 'gov_doc_total'
    elif data_id == 2:
        queryset = cache.get('weibo_doc_total')
        order_column_dict = {}
        doc = WeiboDoc
        cache_key = 'weibo_doc_total'
    elif data_id == 3:
        order_column_dict = {
            '0': "pub_date",
            '1': "area",
            '2': "search_keyword",
            '3': "source",
            '4': "title",
        }
        queryset = cache.get('toutiao_doc_total')
        doc = ToutiaoDoc
        cache_key = 'toutiao_doc_total'
    else:
        logger.error("TABLE UPDATE ERROR: Invalid data_id")
        return JsonResponse(data, safe=False)
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        order_column = request.GET.get('order[0][column]')
        order_direction = request.GET.get('order[0][dir]')
        order_column_str = order_column_dict[order_column]
        # search_value = request.GET.get('search[value]', '')
        if not queryset:
            # print("Queryset not in cache, get from database")
            queryset = doc.objects.all().order_by('-pub_date')[:100]
            print(f"Queryset length: {len(queryset)}")
            cache.set(cache_key, queryset, 7200)
        print(f"Queryset length: {len(queryset)}")
        sorted_queryset = sorted(queryset, key=lambda x: getattr(x, order_column_str),
                                 reverse=True if order_direction == 'desc' else False)
        total_records = len(sorted_queryset)
        page_number = (start // length) + 1
        if data_id == 1:
            data = [{'发布日期': obj.pub_date,
                     '地区': obj.area,
                     '类型': obj.types,
                     '标题': obj.title,
                     '来源': obj.source,
                     '级别': obj.level, }
                    for obj in sorted_queryset[(page_number - 1) * length:page_number * length]]
        elif data_id == 2:
            data = []
        elif data_id == 3:
            data = [{'发布日期': obj.pub_date,
                     '地区': obj.area,
                     '搜索关键词': obj.search_keyword,
                     '标题': obj.title,
                     '来源': obj.source, }
                    for obj in sorted_queryset[(page_number - 1) * length:page_number * length]]
        response = {'draw': draw, 'recordsTotal': total_records, 'recordsFiltered': total_records, 'data': data}
        return JsonResponse(response)
    except Exception as e:
        logger.error(f"TABLE UPDATE ERROR:{e}")
        return JsonResponse(data, safe=False)


# @cache_page(72000)
def wordcloud(request, data_id):
    logger.info('wordcloud start')
    if data_id == 1:
        word_freq_aggr = GovDocWordFreqAggr
    elif data_id == 2:
        return JsonResponse({'word_freq': [{'name': '@TEST@', 'value': 1}]})
    elif data_id == 3:
        word_freq_aggr = ToutiaoDocWordFreqAggr
        pass
    else:
        return JsonResponse({'word_freq': [{'name': '@TEST@', 'value': 1}]})
    distinct_areas = word_freq_aggr.objects.values('area').distinct()
    area_list = [area_dict['area'] for area_dict in distinct_areas]
    # dropdown_list=[{"name":item }for item in area_list]
    area_dict_list = [{'id': str(_), 'name': area} for _, area in enumerate(area_list)]
    area_dict = {item['id']: item['name'] for item in area_dict_list}
    area_id = request.GET.get('region_id')
    # print("\n---\nareaid:", area_id)
    # print(area_id in area_dict)
    if area_id in area_dict:
        # print(area_dict[area_id])
        search_area = area_dict[area_id]
    else:
        return JsonResponse({'word_freq': [{'name': '@TEST@', 'value': 1}]})
    aggregated_words = word_freq_aggr.objects.filter(area=search_area).order_by('-freq')[:500]
    word_freq = [{'name': word.word, 'value': word.freq} for word in aggregated_words]
    context = {'word_freq': word_freq, 'area_list': area_dict_list}
    logger.info('wordcloud end')
    return JsonResponse(context)


@cache_page(72000)
def get_word_hotness(request, data_id):
    try:
        data_id = int(data_id)
    except Exception as _:
        logger.error(f"Invalid data_id:{data_id}\n{_}")
        return JsonResponse({})
    # 获取当前年份
    current_year = datetime.datetime.now().year

    # 计算十年前的年份
    ten_years_ago = current_year - 9

    # 查询datatype为1，近十年的word和freq组合
    results = WordHotness.objects.filter(datatype=data_id, year__gte=ten_years_ago).values('word', 'freq', 'year')
    word_list = set([item['word'] for item in results])
    # 把result按照word_list里面的word进行分组
    word_freq = {}
    for word in word_list:
        word_freq[word] = {}
        for item in results:
            if item['word'] == word:
                word_freq[word][item['year']] = item['freq']
    # data = [{'word': item['word'], 'freq': item['freq'], 'year': item['year']} for item in results]
    return JsonResponse({'word_freq': word_freq})


def process_upload_queue(request, data_id):
    file_dir = os.path.join(settings.BASE_DIR, 'DATA', str(data_id))
    if data_id == 1:
        logger.info('gov_data_import')
        push_queue(queue=file_upload_queue, start_event=file_upload_start_event, task=gov_data_import, delay=60,
                   args=(file_dir,))
        return JsonResponse({'status': 'success', 'msg': 'gov_data_import'})
    elif data_id == 2:
        logger.info('weibo_data_import')
        push_queue(queue=file_upload_queue, start_event=file_upload_start_event, task=test_celery_task, delay=60,
                   args=(file_dir, '11111', '22222'))
        return JsonResponse({'status': 'success', 'msg': 'weibo_data_import'})
    elif data_id == 3:
        logger.info('toutiao_data_import')
        push_queue(queue=file_upload_queue, start_event=file_upload_start_event, task=toutiao_data_import, delay=60,
                   args=(file_dir,))
        # add_task(task=toutiao_data_import, delay=3600, args=(file_dir,))
        return JsonResponse({'status': 'success', 'msg': 'toutiao_data_import'})
    else:
        logger.error('data_id error')
        return JsonResponse({'status': 'error', 'msg': 'data_id error'})
