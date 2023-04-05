# -*- coding: utf-8 -*-
import concurrent.futures
import logging
import math
import multiprocessing
import os
import re

import jieba
import pandas as pd
from django.core.paginator import Paginator
from django.db import connections, transaction
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from utils.json_load import json_load
from .models import GovAggr, GovAggrWordFreq

# os.system('chcp')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
# 定义一个格式字符串，包括时间戳、日志级别和日志消息
format_string = "%(asctime)s - %(levelname)s - %(message)s"
# 创建一个 Formatter 对象，并将格式字符串传递给它
formatter = logging.Formatter(format_string)
# 将 Formatter 应用于处理器
console_handler.setFormatter(formatter)
# 将处理器添加到日志记录器中
logger.addHandler(console_handler)


# Create your views here.
def index(response):
    # return
    return render(response, 'dataDemo.html')


def data_import(response, filepath: str = r"D:\Programs\Code\python\projects\info_system\DATA\政府网站数据\数据汇总"):
    os.system('chcp 65001')
    # logging.getLogger().setLevel(logging.INFO)
    logging.info("导入数据中")
    os.system('chcp')
    try:
        data_json = json_load(filepath)
        area_pattern = re.compile(r'[^\d-]+')
        # time_pattern = re.compile(r'\W*\d{4}年\d+月\d{1,2}日\W*')

        for name_key, value_list in data_json.items():
            logging.info(f"读取文件：{name_key}")
            # 匹配地区名
            match_res = area_pattern.search(name_key)
            if match_res and match_res.group()[-2:] == "文件":
                area = match_res.group()[:-2]
            else:
                logging.error('地区名称读取失败')
                area = ''
                # raise ValueError("地区名称读取失败")

            key_map = {
                'link': ['link', '链接', 'url', 'pagelink_id'],
                'title': ['title', '标题'],
                'content': ['正文内容'],
                'pub_date': ['发布日期'],
                'source': ['department', '来源'],
                'level': ['级别'],
                'types': ['类别', '文件类型', 'type', '新闻类型', '类型']
            }

            for item in value_list:
                result = {
                    'link': '',
                    'title': '',
                    'content': '',
                    'pub_date': None,
                    'source': '',
                    'level': '',
                    'types': ''
                }
                for map_key, alternatives in key_map.items():
                    if map_key == 'types':
                        for alt_key in alternatives:
                            if alt_key in item:
                                result[map_key] += str(item[alt_key]) + ' '
                    else:
                        for alt_key in alternatives:
                            if alt_key in item:
                                result[map_key] = str(item[alt_key])
                                # if map_key not in ['pub_date'] else item[alt_key]
                                break
                    result[map_key] = result[map_key].strip()

                # 处理发布日期
                if result['pub_date']:
                    timestring = result['pub_date']
                    temp_date = pd.to_datetime(timestring, errors='coerce')
                    if temp_date is pd.NaT:
                        temp_date = pd.to_datetime(timestring, format="%Y年%m月%d日", errors='coerce')
                    temp_date = temp_date if temp_date is not pd.NaT else None
                    result['pub_date'] = temp_date
                else:
                    result['pub_date'] = None

                types = result['types']
                link = result['link'][:2000]
                title = result['title'][:500]
                content = result['content'][:10000]
                pub_date = result['pub_date']
                source = result['source'][:50]
                level = result['level']
                if GovAggr.objects.filter(area=area, title=title).exists():
                    continue
                if pub_date and not GovAggr.objects.filter(area=area, title=title, pub_date=pub_date).exists():
                    update_fields = {
                        'area': area, 'types': types, 'link': link,
                        'title': title, 'content': content,
                        'pub_date': pub_date, 'source': source,
                        'level': level
                    }
                    data_model = GovAggr(**update_fields)
                else:
                    update_fields = {
                        'area': area, 'types': types, 'link': link,
                        'title': title, 'content': content, 'source': source,
                        'level': level
                    }
                    data_model = GovAggr(**update_fields)
                data_model.save()
        logging.info("输出结束")
        return HttpResponse("写入完成")
    except Exception as e:
        logging.error(f"ERROR:{e}")
        # print(response)
    return JsonResponse({'info': "数据汇总表写入完成", 'response': str(response)})


def table_update(request):
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        # search_value = request.GET.get('search[value]', '')
        queryset = GovAggr.objects.all().order_by('-pub_date')
        total_records = queryset.count()

        paginator = Paginator(queryset, length)
        page_number = (start // length) + 1
        data = [{'发布日期': obj.pub_date, '地区': obj.area, '类型': obj.types, '标题': obj.title, '链接': obj.link,
                 '正文': obj.content}
                for obj in paginator.get_page(page_number)]
        response = {'draw': draw, 'recordsTotal': total_records, 'recordsFiltered': total_records, 'data': data}
        return JsonResponse(response)
    except Exception as e:
        data = {'request': request}
        logging.error(f"ERROR:{e}")
        return JsonResponse(data, safe=False)


def word_split(request):
    logging.info("start splitting")
    articles = GovAggr.objects.filter(is_split=False)
    # 加载停用词
    stopwords = []
    with open('datas/stopwords.txt', 'r', encoding='utf-8') as f:
        for line in f:
            stopwords.append(line.strip())
    cpu_count = multiprocessing.cpu_count()
    # cpu_count = 2
    all_records = articles.count()
    record_per_process = math.ceil(all_records / cpu_count)
    # pool = multiprocessing.Pool(processes=cpu_count)
    # for _ in range(cpu_count):
    #     start = _ * record_per_process
    #     end = (_ + 1) * record_per_process
    #     model_list = articles[start:end]
    #     pool.apply_async(word_split_multiprocess_task, args=(model_list, stopwords))
    #     print(f"multiprocess {_} start\n")
    # pool.close()
    # pool.join()

    # 使用ThreadPoolExecutor替代multiprocessing.Pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=cpu_count) as executor:
        futures = []
        for _ in range(cpu_count):
            start = _ * record_per_process
            end = (_ + 1) * record_per_process
            model_list = articles[start:end]
            future = executor.submit(word_split_multiprocess_task, model_list, stopwords)
            futures.append(future)
            logging.info(f"thread {_} start\n")

        # 等待所有线程完成
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f"Writing:{e}")
    logging.info("----------finished----------")
    # articles.update(is_split=True)
    # print(request)
    return HttpResponse("分词中")


def word_split_multiprocess_task(model_list, stopwords):
    # 获取默认数据库的连接
    connection = connections['default']
    # 关闭连接并确保重新建立连接
    connection.close()
    connection.ensure_connection()

    # 使用游标执行原生SQL查询
    with connection.cursor() as _:
        stop_pattern = re.compile(r'[\s\d\u2002\u2003\u3000\xa0二三四五六七八九]')
        for article in model_list:
            with transaction.atomic():
                # 分词并词频统计
                seg_list = jieba.lcut(article.content)
                word_freq = {}
                for word in seg_list:
                    # if len(word) == 1:
                    #     continue
                    # 去除停用词和数字,标点符号
                    if word in stopwords or stop_pattern.search(word):
                        continue
                    word_freq[word] = word_freq.get(word, 0) + 1
                word_model_list = []
                unique_word_models = set()
                for word, freq in word_freq.items():
                    if (word, article.id) in unique_word_models or GovAggrWordFreq.objects.filter(word=word, record=article).exists():
                        continue
                    else:
                        word_freq_model = GovAggrWordFreq(word=word, freq=freq, record=article)
                        word_model_list.append(word_freq_model)
                        unique_word_models.add((word, article.id))
                if len(word_model_list):
                    GovAggrWordFreq.objects.bulk_create(word_model_list)
                article.is_split = True
                article.save()
                logging.info(f"article {article.id} saved")


@cache_page(7200)
def wordcloud(request):
    logging.info('start')
    aggregated_words = GovAggrWordFreq.objects.values('word').annotate(total_freq=Sum('freq')).order_by('-total_freq')[:1000]
    print(len(aggregated_words))
    word_freq = [{'name': word['word'], 'value': word['total_freq']} for word in aggregated_words]
    # word_freq = word_freq[:1000]
    context = {'word_freq': word_freq}
    logging.info('end')
    return JsonResponse(context)
