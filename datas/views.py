# -*- coding: utf-8 -*-
import concurrent.futures
import logging
import math
import multiprocessing
# import multiprocessing
import os
import re
import time
from collections import defaultdict
from typing import Union

import jieba
import pandas as pd
from django.conf import settings
from django.core.paginator import Paginator
from django.db import connections, transaction
from django.db.models import F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from utils.json_load import load_forms, generate_id
from .models import GovDoc, GovDocWordFreq, GovDocWordFreqAggr

logger = logging.getLogger('django')


# Create your views here.
def index(response):
    # return
    return render(response, 'dataDemo.html')


def gov_data_import(response, filepath: str = settings.BASE_DIR / "DATA/政府网站数据/数据汇总"):
    logger.info("政府汇总数据导入中")
    logger.info(f"读取文件：{filepath}")
    try:
        data_json = load_forms(filepath)
        area_pattern = re.compile(r'[^\d-]+')
        # time_pattern = re.compile(r'\W*\d{4}年\d+月\d{1,2}日\W*')

        for name_key, value_list in data_json.items():
            logger.debug(f"读取文件：{name_key}")
            # 匹配地区名
            match_res = area_pattern.search(name_key)
            if match_res and match_res.group()[-2:] == "文件":
                area = match_res.group()[:-2]
            else:
                logger.error('地区名称读取失败')
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
                                result[map_key] = str(item[alt_key]) if item[alt_key] else ''
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

                types = result['types'][:500]
                link = result['link']
                title = result['title'][:500]
                content = result['content']
                pub_date = result['pub_date']
                source = result['source'][:50]
                level = result['level'][:50]
                if GovDoc.objects.filter(area=area, title=title).exists():
                    continue
                if pub_date and not GovDoc.objects.filter(area=area, title=title, pub_date=pub_date).exists():
                    update_fields = {
                        'area': area, 'types': types, 'link': link,
                        'title': title, 'content': content,
                        'pub_date': pub_date, 'source': source,
                        'level': level
                    }
                    data_model = GovDoc(**update_fields)
                else:
                    update_fields = {
                        'area': area, 'types': types, 'link': link,
                        'title': title, 'content': content, 'source': source,
                        'level': level
                    }
                    data_model = GovDoc(**update_fields)
                data_model.save()
        logger.info("政府汇总数据读取写入完成")
        return HttpResponse("写入完成")
    except Exception as e:
        logging.error(f"ERROR:{e}")
    return JsonResponse({'info': "数据汇总表写入完成"})


@cache_page(7200)
def table_update(request):
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        # search_value = request.GET.get('search[value]', '')
        queryset = GovDoc.objects.all().order_by('-pub_date')
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


def word_split(request):
    logger.info("start word splitting")
    articles = GovDoc.objects.filter(is_split=False)
    # 加载停用词
    stopwords = set()
    stopwords_file_path = os.path.join(settings.STATIC_ROOT, 'stopwords.txt')
    with open(stopwords_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            stopwords.add(line.strip())
        stop_pattern = re.compile(r'[\s\u2002\u2003\u3000\u200b\u200d\xa0\x7f\d二三四五六七八九.]')

    cpu_count = multiprocessing.cpu_count() * 2 if multiprocessing.cpu_count() < 17 else 32
    all_records = articles.count()
    record_per_process = math.ceil(all_records / cpu_count)

    # 使用ThreadPoolExecutor替代multiprocessing.Pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=cpu_count) as executor:
        futures = []
        try:
            import jieba_fast
            tokenizer = jieba_fast.Tokenizer()  # 创建分词器实例
        except Exception as _:
            logger.error(f"{_}:jieba_fast not found, use jieba instead")
            tokenizer = jieba.Tokenizer()  # 创建分词器实例

        for _ in range(cpu_count):
            logger.debug(f"thread {_} start")
            start = _ * record_per_process
            end = (_ + 1) * record_per_process
            model_list = articles[start:end]
            params = {
                'model_list': model_list,
                'tokenizer': tokenizer,
                'stopwords': stopwords,
                'stop_pattern': stop_pattern,
                'thread': _
            }
            future = executor.submit(word_split_multiprocess_task, **params)
            futures.append(future)
            logger.debug(f"thread {_} end")

        # 等待所有线程完成
        for future in concurrent.futures.as_completed(futures):
            word_total_models = future.result()
            for uid in word_total_models:
                retries = 0
                max_retries = 50
                while retries < max_retries:
                    try:
                        # 把model 字典里的同名下的值分别赋给word,area,freq
                        model = GovDocWordFreq.objects.get(id=uid)
                        word, freq, record_id = model.word, model.freq, model.record_id
                        area = GovDoc.objects.get(id=record_id).area
                        with transaction.atomic():
                            update_rows = GovDocWordFreqAggr.objects.filter(word=word,
                                                                            area=area).select_for_update().update(
                                freq=F('freq') + freq)
                            if update_rows == 0:
                                GovDocWordFreqAggr.objects.create(word=word, area=area, freq=freq)
                            update_rows = GovDocWordFreqAggr.objects.filter(word=word,
                                                                            area='TOTAL').select_for_update().update(
                                freq=F('freq') + freq)
                            if update_rows == 0:
                                GovDocWordFreqAggr.objects.create(word=word, area='TOTAL', freq=freq)
                        # future.result()
                    except Exception as e:
                        if 'Deadlock found' in str(e):  # 如果是死锁异常，尝试重试
                            retries += 1
                            time.sleep(0.5)  # 等待0.5秒后重试
                            if retries == max_retries:
                                logger.error(f"WordFreqAggr UID:{uid} Updating:{e} (Reached max retries)")
                                with open(file=os.path.join(settings.STATIC_ROOT, 'logs', 'wrong_result.txt'),
                                          mode='a',
                                          encoding='utf-8') as f:
                                    if word and freq and area:
                                        f.write(f"\nUID_{uid} {word} {freq} {area}")
                                    else:
                                        f.write(f"\nUID_{uid}")
                        else:
                            logger.error(f"WordFreqAggr UID:{uid} Updating:{e}")
                            with open(file=os.path.join(settings.STATIC_ROOT, 'logs', 'wrong_result.txt'),
                                      mode='a',
                                      encoding='utf-8') as f:
                                if word and freq and area:
                                    f.write(f"\nUID_{uid} {word} {freq} {area}")
                                else:
                                    f.write(f"\nUID_{uid}")
                            break
                    else:
                        logger.debug(f"WordFreqAggr UID:{uid} Updated")
                        break
        logger.info("----------All Thread finished----------")
        return HttpResponse("分词结束")


def word_split_multiprocess_task(model_list: list = None,
                                 tokenizer: Union[jieba.Tokenizer, 'jieba_fast.Tokenizer'] = None,
                                 stopwords: Union[set, list] = None,
                                 stop_pattern: re.compile = re.compile(r'\s'),
                                 worker=999):
    # 获取默认数据库的连接
    if stopwords is None:
        stopwords = []
    if model_list is None:
        model_list = []
    if tokenizer is None:
        tokenizer = jieba.Tokenizer()
    connection = connections['default']
    # 关闭连接并确保重新建立连接
    connection.close()
    connection.ensure_connection()
    # 使用游标执行原生SQL查询
    # with connection.cursor() as _:

    word_total_models = []
    for article in model_list:
        # 分词并词频统计
        with defaultdict(int) as word_freq:
            for word in tokenizer.cut(article.content):
                # 去除停用词和数字,标点符号,并转换为小写
                if word in stopwords or stop_pattern.search(word):
                    continue
                word = word if not word.isalpha() else word.lower()
                # 词频统计
                word_freq[word] += 1

            # 保存词频统计结果写入数据表
            word_model_list = []
            with set() as unique_word_models:
                for word, freq in word_freq.items():
                    if (word, article.id) in unique_word_models:
                        continue
                    uid = generate_id(word, article.id)
                    if GovDocWordFreq.objects.filter(id=uid).exists():
                        continue
                    else:
                        word_freq_model = GovDocWordFreq(id=uid, word=word, freq=freq, record=article)
                        # area = GovDoc.objects.get(id=article.id).area
                        word_model_list.append(word_freq_model)
                        unique_word_models.add((word, article.id))
                        word_total_models.append(uid)
            try:
                with transaction.atomic():
                    if word_model_list:
                        GovDocWordFreq.objects.bulk_create(word_model_list)
                    article.is_split = True
                    article.save(update_fields=['is_split'])
                    logger.debug(f"article:{article.id} save success with WORKER:{worker}")
            except Exception as e:
                logger.error(f"bulk transaction error:{e} with WORKER:{worker}")
            finally:
                # 销毁word_model_list
                del word_model_list

    return word_total_models


@cache_page(7200)
def wordcloud(request):
    logger.info('wordcloud start')
    aggregated_words = GovDocWordFreqAggr.objects.filter(area='TOTAL').order_by('-freq')[:1000]
    word_freq = [{'name': word.word, 'value': word.freq} for word in aggregated_words]
    context = {'word_freq': word_freq}
    logger.info('wordcloud end')
    return JsonResponse(context)
