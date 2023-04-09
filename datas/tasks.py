import concurrent.futures
import gc
import logging
import math
import multiprocessing
import os
import re
from collections import defaultdict
from typing import Union

import jieba
import pandas as pd
from django.conf import settings
from django.db import transaction, connections

from datas.models import GovDoc, GovDocWordFreq, GovDocWordFreqAggr
from datas.utils import get_stopwords
from utils.json_load import load_forms
from utils.utils import generate_id

logger = logging.getLogger('django')


def gov_data_import(filepath: str = settings.BASE_DIR / "DATA/政府网站数据/数据汇总"):
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
        return "success"
    except Exception as e:
        logging.error(f"ERROR:{e}")
        return "error"


def read_wrong_result(output_file: str):
    read_uids = []
    failed_read_uids = []  # 记录更新失败的uid
    # 读取result.txt结果，解析为uid的list
    with open(file=output_file, mode='r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        try:
            if "UID_" in line:
                read_uids.append(int(line.strip()[4:]))
            else:
                read_uids.append(int(line.strip()))
            yield read_uids  # TODO
        except Exception as _:
            logger.error(f"READ ERROR:{_}")
            failed_read_uids.append(line.strip())

    if failed_read_uids:
        with open(file=output_file, mode='w', encoding='utf-8') as f:
            f.write('\n'.join(uid for uid in failed_read_uids))
    else:
        with open(file=output_file, mode='w', encoding='utf-8') as f:
            f.write('')


# 使用chunked方法分批获取数据库记录，避免一次性加载大量数据占用内存
# 在循环中使用try-finally语句，确保数据处理后释放内存。使用gc.collect()手动调用垃圾回收机制，释放不再使用的内存。
# 减少不必要的内存拷贝：如果可以避免复制大量的数据，就可以减少内存的使用。例如，在循环中不要反复拷贝大数据块，可以复用缓冲区。
# 使用生成器：生成器可以避免在内存中同时存储所有数据。可以使用生成器来逐个读取数据并进行处理。
# 使用列表解析器：列表解析器可以用更少的代码完成列表的创建，而且在某些情况下，列表解析器比for循环更快。
# 使用内存映射文件：内存映射文件可以将大型文件映射到虚拟内存中。这样，可以像操作常规数组一样操作文件中的数据，而不必将整个文件读入内存。
def word_split():
    logger.info("start word splitting")
    cpu_count = multiprocessing.cpu_count() * 2 if multiprocessing.cpu_count() < 17 else 32

    # 使用ThreadPoolExecutor替代multiprocessing.Pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=cpu_count) as executor:
        futures = []
        futures_dict = {}

        try:
            import jieba_fast
            tokenizer = jieba_fast.Tokenizer()  # 创建分词器实例
        except Exception as _:
            logger.error(f"{_}:jieba_fast not found, use jieba instead")
            tokenizer = jieba.Tokenizer()  # 创建分词器实例

        # 加载停用词
        stopwords, stop_pattern = get_stopwords()

        articles = GovDoc.objects.filter(is_split=False)
        # record_per_process = math.ceil(articles.count() / cpu_count)
        iterator = articles.iterator(chunk_size=articles.count() // cpu_count + 1)

        thread = 0
        for chunk in iterator:
            logger.debug(f"WORKER {thread} start")
            params = {
                'model_list': chunk,
                'tokenizer': tokenizer,
                'stopwords': stopwords,
                'stop_pattern': stop_pattern,
                'worker': _
            }
            future = executor.submit(word_split_multiprocess_task, **params)
            futures.append(future)
            futures_dict[str(thread)] = future

        results = []
        # 等待所有线程完成
        output_file = os.path.join(settings.BASE_DIR, 'logs', 'wrong_result.txt')
        for future in concurrent.futures.as_completed(futures):
            for key, values in futures_dict.items():
                if values == future:
                    logger.debug(f"WORKER {key} finish")
                    break
            word_total_models = future.result()
            read_uids = read_wrong_result(output_file)

            # 将uid按每批1000个进行划分
            batch_size = 1000
            uid_batches = [word_total_models[i:i + batch_size] for i in range(0, len(word_total_models), batch_size)]
            failed_uids = []  # 记录更新失败的uid
            for uid_batch in uid_batches:
                word_aggr_updates = defaultdict(lambda: defaultdict(int))
                for uid in uid_batch:
                    model = GovDocWordFreq.objects.get(id=uid)
                    word, freq, record_id = model.word, model.freq, model.record_id
                    area = GovDoc.objects.get(id=record_id).area
                    # TODO sql缓存 redis等缓存系统
                    word_aggr_updates[word][area] += freq
                    word_aggr_updates[word]['TOTAL'] += freq

                # Prepare the list of objects to be updated
                update_list = []
                for word, freq_dict in word_aggr_updates.items():
                    for area, freq in freq_dict.items():
                        aggr_obj, created = GovDocWordFreqAggr.objects.get_or_create(word=word,
                                                                                     area=area,
                                                                                     defaults={'freq': 0})
                        aggr_obj.freq += freq_dict[area]
                        update_list.append(aggr_obj)

                max_retries = cpu_count * 2 if cpu_count < 25 else 50
                for retries in range(max_retries):
                    # Perform the bulk update
                    with transaction.atomic():
                        try:
                            GovDocWordFreqAggr.objects.bulk_update(update_list, ['freq'])
                        except Exception as e:
                            transaction.set_rollback(True)
                            if retries == max_retries - 1:
                                failed_uids.extend(uid_batch)
                                logger.error(f"WordFreqAggr Updating:{e}")
                                break
                        else:
                            logger.debug("WordFreqAggr Updated")
                            break
                            # 更新失败，将失败的uid记录下来
                # 将更新失败的uid写入到result.txt中
                if failed_uids:
                    with open(file=output_file, mode='a', encoding='utf-8') as f:
                        f.write('\n'.join(str(uid) for uid in failed_uids))
                del word_aggr_updates
                del uid_batch
                del uid_batches
            del word_total_models
            gc.collect()
        logger.info("----------All Thread finished----------")
        return "分词结束"


def word_split_multiprocess_task(model_list_generator,
                                 tokenizer: Union[jieba.Tokenizer, 'jieba_fast.Tokenizer'] = None,
                                 stopwords: Union[set, list] = None,
                                 stop_pattern: re.compile = re.compile(r'\s'),
                                 worker=999):
    # 获取默认数据库的连接
    if stopwords is None:
        stopwords = []
    if tokenizer is None:
        tokenizer = jieba.Tokenizer()
    connection = connections['default']
    # 关闭连接并确保重新建立连接
    connection.close()
    connection.ensure_connection()
    # 使用游标执行原生SQL查询
    # with connection.cursor() as _:

    word_total_models = []
    for model_list in model_list_generator:
        for article in model_list:
            # 分词并词频统计
            word_freq = defaultdict(int)
            for word in tokenizer.cut(article.content):
                # 去除停用词和数字,标点符号,并转换为小写
                if word in stopwords or stop_pattern.search(word):
                    continue
                word = word if not word.isalpha() else word.lower()
                # 词频统计
                word_freq[word] += 1

            # 保存词频统计结果写入数据表
            word_model_list = []
            unique_word_models = set()
            for word, freq in word_freq.items():
                if (word, article.id) in unique_word_models:
                    continue
                uid = generate_id(word, article.id)
                if GovDocWordFreq.objects.filter(id=uid).exists():
                    continue
                else:
                    word_freq_model = GovDocWordFreq(id=uid, word=word, freq=freq, record=article)
                    word_model_list.append(word_freq_model)
                    unique_word_models.add((word, article.id))
                    word_total_models.append(uid)
            del unique_word_models
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
            del word_freq
        gc.collect()
    return word_total_models
