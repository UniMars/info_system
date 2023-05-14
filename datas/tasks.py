import concurrent.futures
import datetime
import gc
import logging
import multiprocessing
import os
import re
import time
from collections import defaultdict
from typing import Union

import jieba
from celery import shared_task
from django.conf import settings
from django.db import transaction, connections
from django.db.models import Sum, ForeignKey, Q
from django.db.models.expressions import RawSQL

from datas.models import GovDoc, GovDocWordFreq, ToutiaoDoc, WordHotness, ToutiaoDocWordFreq, ToutiaoDocWordFreqAggr, \
    GovDocWordFreqAggr
from datas.utils.json_load import load_forms
from datas.utils.utils import generate_id, get_stopwords, get_gov_doc_name, unpack_result, convert_date, \
    read_wrong_result

# logger = logging.getLogger('django')
logger = logging.getLogger('tasks')


@shared_task
def gov_data_import(filepath: str = ""):
    if not filepath:
        filepath = settings.BASE_DIR / "DATA/1"
    logger.info("政府汇总数据导入中")
    logger.info(f"读取文件：{filepath}")
    try:
        for name_key, value_list in load_forms(filepath, if_move=True):
            area = get_gov_doc_name(name_key)
            key_map = {
                'link': {"alternatives": ['link', '链接', 'url', 'pagelink_id'], "read_type": "or", },
                'title': {"alternatives": ['title', '标题'], "read_type": "or", },
                'content': {"alternatives": ['正文内容'], "read_type": "or", },
                'pub_date': {"alternatives": ['发布日期'], "read_type": "or", },
                'source': {"alternatives": ['department', '来源'], "read_type": "or", },
                'level': {"alternatives": ['级别'], "read_type": "or", },
                'types': {"alternatives": ['类别', '文件类型', 'type', '新闻类型', '类型'], "read_type": "and", },
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
                unpack_result(item, key_map, result)

                # 处理发布日期
                result['pub_date'] = convert_date(result['pub_date'])

                (link, title, content, pub_date, source, level, types) = result.values()

                title = title[:500]
                source = source[:50]
                level = level[:50]
                types = types[:500]
                if not pub_date:
                    pub_date = datetime.datetime(1900, 1, 1)
                if GovDoc.objects.filter(area=area, title=title, pub_date=pub_date).exists():
                    continue
                update_fields = {
                    'area': area, 'types': types, 'link': link,
                    'title': title, 'content': content,
                    'pub_date': pub_date, 'source': source,
                    'level': level
                }
                data_model = GovDoc(**update_fields)
                data_model.save()
        logger.info("政府汇总数据读取写入完成")
        return "success"
    except Exception as e:
        logging.error(f"ERROR:{e}")
        return "error"
    finally:
        word_split(1)


@shared_task
def toutiao_data_import(rootpath: str = ""):
    if not rootpath:
        rootpath = settings.BASE_DIR / "DATA/3"
    logger.info("头条数据导入中")
    logger.info(f"读取文件：{rootpath}")
    try:
        # data_json = load_forms(rootpath, if_move=False)
        for name_key, value_list in load_forms(rootpath, if_move=True):
            unique_set = set()
            bulk_list = []
            key_map = {
                'title': {"alternatives": ['title', '标题'], "read_type": "or", },
                'link': {"alternatives": ['url', 'link', '链接', 'pagelink_id'], "read_type": "or", },
                'area': {"alternatives": ['area_keyword'], "read_type": "or", },
                'search_keyword': {"alternatives": ['search_keyword'], "read_type": "or", },
                'pub_date': {"alternatives": ['date', '发布日期'], "read_type": "or", },
                'source': {"alternatives": ['media', 'department', '来源'], "read_type": "or", },
                'content': {"alternatives": ['context', '正文内容'], "read_type": "or", },
                'comment': {"alternatives": ['comment', '评论'], "read_type": "or", },
            }
            for item in value_list:
                result = {
                    'title': '',
                    'link': '',
                    'area': '',
                    'search_keyword': '',
                    'pub_date': None,
                    'source': '',
                    'content': '',
                    'comment': '',
                }
                unpack_result(item, key_map, result)

                # 处理发布日期
                result['pub_date'] = convert_date(result['pub_date'])

                (title, link, area, search_keyword, pub_date, source, content, comment) = result.values()
                search_keyword = search_keyword[:50]
                title = title[:500]
                source = source[:50]

                if not pub_date:
                    pub_date = datetime.datetime(1900, 1, 1)
                if ToutiaoDoc.objects.filter(area=area, title=title, pub_date=pub_date).exists():
                    continue
                if (title, pub_date) in unique_set:  # 去重
                    continue
                unique_set.add((title, pub_date))
                update_fields = {
                    'title': title,
                    'link': link,
                    'area': area,
                    'search_keyword': search_keyword,
                    'pub_date': pub_date,
                    'source': source,
                    'content': content,
                    'comment': comment
                }
                data_model = ToutiaoDoc(**update_fields)
                bulk_list.append(data_model)
                # data_model.save()
            with transaction.atomic():
                ToutiaoDoc.objects.bulk_create(bulk_list)
                bulk_list.clear()
            print(f"头条数据导入完成：{name_key}")
    except Exception as e:
        logging.error(f"ERROR:{e}")
        return "error"
    finally:
        word_split(3)


# 使用chunked方法分批获取数据库记录，避免一次性加载大量数据占用内存
# 在循环中使用try-finally语句，确保数据处理后释放内存。使用gc.collect()手动调用垃圾回收机制，释放不再使用的内存。
# 减少不必要的内存拷贝：如果可以避免复制大量的数据，就可以减少内存的使用。例如，在循环中不要反复拷贝大数据块，可以复用缓冲区。
# 使用生成器：生成器可以避免在内存中同时存储所有数据。可以使用生成器来逐个读取数据并进行处理。
# 使用列表解析器：列表解析器可以用更少的代码完成列表的创建，而且在某些情况下，列表解析器比for循环更快。
# 使用内存映射文件：内存映射文件可以将大型文件映射到虚拟内存中。这样，可以像操作常规数组一样操作文件中的数据，而不必将整个文件读入内存。
@shared_task
def word_split(data_type):
    # logger.debug("hello world------")
    if data_type == 1:
        doc = GovDoc
        word_freq = GovDocWordFreq
    elif data_type == 2:
        return
    elif data_type == 3:
        doc = ToutiaoDoc
        word_freq = ToutiaoDocWordFreq
    else:
        logger.error('wrong data_type')
        return
    doc_str = doc.__name__
    logger.info(f"start {doc_str} word splitting")
    cpu_count = multiprocessing.cpu_count() * 2 if multiprocessing.cpu_count() < 17 else 32

    # 使用ThreadPoolExecutor替代multiprocessing.Pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=cpu_count) as executor:
        futures = []
        futures_dict = {}
        # 加载jieba_fast
        try:
            import jieba_fast
            tokenizer = jieba_fast.Tokenizer()  # 创建分词器实例
        except Exception as _:
            logger.error(f"{_}:jieba_fast not found, use jieba instead")
            tokenizer = jieba.Tokenizer()  # 创建分词器实例

        # 加载停用词
        stopwords, stop_pattern = get_stopwords()
        output_file = os.path.join(settings.BASE_DIR, 'logs', 'wrong_result.txt')
        articles = doc.objects.filter(is_split=False)
        article_count = articles.count()
        if article_count != 0:
            # logger.info("----------All Thread finished----------")
            # word_freq_sum(data_type=data_type,cpu_count=cpu_count,output_file=output_file)
            # return "分词结束"
            chunk_size = article_count // cpu_count + 1
            chunks = [articles[i:i + chunk_size].iterator() for i in range(0, article_count, chunk_size)]

            thread = 0
            for chunk in chunks:
                logger.debug(f"WORKER {thread} start")
                params = {
                    'model_list_iterator': chunk,
                    'doc_word_freq_model': word_freq,
                    'tokenizer': tokenizer,
                    'stopwords': stopwords,
                    'stop_pattern': stop_pattern,
                    'worker': thread
                }
                future = executor.submit(word_split_multiprocess_task, **params)
                futures.append(future)
                futures_dict[str(thread)] = future
                thread += 1

            # results = []
            # 等待所有线程完成
            for future in concurrent.futures.as_completed(futures):
                for key, values in futures_dict.items():
                    if values == future:
                        logger.debug(f"WORKER {key} finish")
                        break
                word_total_models = future.result()
                read_uids = read_wrong_result(output_file)
                word_total_models.extend(read_uids)
        logger.info("----------All Thread finished----------")
        # word_freq_sum(data_type=data_type,cpu_count=cpu_count,output_file=output_file)
        freq_aggr_sum(data_type=data_type)
        return "分词结束"


def word_split_multiprocess_task(model_list_iterator,
                                 doc_word_freq_model,
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

    word_total_models = []
    gc_count = 0
    time1 = time.perf_counter()
    for article in model_list_iterator:
        # jieba_time_count = 0
        search_time_count = 0
        bulk_time_count = 0
        # bulk_create_count = 0
        # bulk_update_count = 0
        try:
            # 分词并词频统计
            word_freq = defaultdict(int)
            unique_uids = set()
            # jieba_time1=time.perf_counter()
            for word in tokenizer.cut(article.content):
                # 去除停用词和数字,标点符号,并转换为小写
                if word in stopwords or stop_pattern.search(word):
                    continue
                word = word if not word.isalpha() else word.lower()
                # 词频统计
                word_freq[word] += 1
            # jieba_time2=time.perf_counter()
            # jieba_time_count+=jieba_time2-jieba_time1

            search_time1 = time.perf_counter()
            # 保存词频统计结果写入数据表
            word_model_list = []
            for word, freq in word_freq.items():
                uid = generate_id(word, article.id)
                if uid in unique_uids:
                    continue
                if doc_word_freq_model.objects.filter(id=uid).exists():
                    continue
                else:
                    word_model_list.append(
                        doc_word_freq_model(id=uid, word=word, freq=freq, record_id=article.id,
                                            pub_date=article.pub_date))
                    word_total_models.append(uid)
                    unique_uids.add(uid)
            search_time2 = time.perf_counter()
            search_time_count += search_time2 - search_time1

            bulk_time1 = time.perf_counter()
            with transaction.atomic():
                if word_model_list:
                    # bulk_create_time1=time.perf_counter()
                    doc_word_freq_model.objects.bulk_create(word_model_list)
                    # bulk_create_time2=time.perf_counter()
                    # bulk_create_count+=bulk_create_time2-bulk_create_time1
                # bulk_create_time3=time.perf_counter()
                article.is_split = True
                article.save(update_fields=['is_split'])
                # bulk_create_time4=time.perf_counter()
                # bulk_update_count+=bulk_create_time4-bulk_create_time3
                logger.debug(f"article:{article.id} save success with WORKER:{worker}")
            del word_model_list
            del word_freq
            bulk_time2 = time.perf_counter()
            bulk_time_count += bulk_time2 - bulk_time1
        except Exception as e:
            logger.error(f"bulk transaction error:{e} with WORKER:{worker}")
        finally:
            # logger.debug(f"----------------------------------------")
            logger.debug(
                f"Worker {worker} Article {article.id}:\nsearch cost {search_time_count:.4f}s\nbulk cost {bulk_time_count:.4f}s")
            # logger.debug(f"Worker {worker} Article {article.id}:\nbulk_create cost{bulk_create_count}s\nupdate cost{bulk_update_count}s")
            # logger.debug(f"----------------------------------------")
            gc_count += 1
            if gc_count == 500:
                gc_count = 0
                gc.collect()
                # 销毁word_model_list
    time2 = time.perf_counter()
    logger.debug(f"WORKER:{worker} cost {int(time2 - time1)}s")
    return word_total_models


def bulk_update_or_create(word_freqs, freq_aggr_model, batch_size=10000, area_key=""):
    logger.info(f"bulk_update_or_create {freq_aggr_model} start")
    # 聚合所有区域的词频总和
    to_update = []
    to_create = []
    count_update = 1
    count_create = 1
    # word_freq_count=word_freqs.count()
    total_count = 0
    # 更新 freq_aggr_model 表
    for word_freq in word_freqs:
        area = word_freq['record__area'] if area_key == "" else area_key
        word = word_freq['word']
        total_freq = word_freq['total_freq']

        # 查询 freq_aggr_model 中是否存在相应的记录
        area_word_freq_obj = freq_aggr_model.objects.filter(area=area,
                                                            word=word).first()

        # 如果记录存在，则更新；否则，创建新记录
        if area_word_freq_obj:
            if area_word_freq_obj.freq == total_freq:
                continue
            area_word_freq_obj.freq = total_freq
            to_update.append(area_word_freq_obj)
            count_update += 1
        else:
            area_word_freq_obj = freq_aggr_model(area=area,
                                                 word=word,
                                                 freq=total_freq)
            to_create.append(area_word_freq_obj)
            count_create += 1

        # 执行bulk操作
        if count_update % batch_size == 0:
            total_count += batch_size
            logger.info(f"to_update: {total_count}")
            freq_aggr_model.objects.bulk_update(to_update, ['freq'])
            count_update = 1
            to_update = []
            gc.collect()
        if count_create % 10000 == 0:
            total_count += batch_size
            logger.info(f"to_create: {total_count}")
            freq_aggr_model.objects.bulk_create(to_create)
            count_create = 1
            to_create = []
            gc.collect()
    if to_update:
        logger.info(f"finally to_update: {count_update}")
        freq_aggr_model.objects.bulk_update(to_update, ['freq'])
    if to_create:
        logger.info(f"finally to_create: {count_create}")
        freq_aggr_model.objects.bulk_create(to_create)
    logger.info("Bulk update Done!")


def freq_aggr_sum(data_type=0, start_time=None):
    if data_type == 1:
        doc_str = "GovDoc"
        doc = GovDoc
        word_freq = GovDocWordFreq
        word_freq_aggr = GovDocWordFreqAggr
    elif data_type == 2:
        return
    elif data_type == 3:
        doc_str = "ToutiaoDoc"
        doc = ToutiaoDoc
        word_freq = ToutiaoDocWordFreq
        word_freq_aggr = ToutiaoDocWordFreqAggr
    else:
        logger.error('wrong data_type')
        return
    logger.info(f'{doc_str} freq sum start')
    fks = [i for i in word_freq._meta.fields if i.name == "record_id" and isinstance(i, ForeignKey)]
    if fks:
        # 筛选发布时间大于指定日期的记录
        if start_time:
            area_word_freqs = word_freq.objects.filter(
                pub_date__gt=start_time).values(
                'record_id__area', 'word').annotate(total_freq=Sum('freq')).iterator()
        else:
            area_word_freqs = word_freq.objects.values(
                'record_id__area', 'word').annotate(total_freq=Sum('freq')).iterator()
    else:
        rawsql = RawSQL(
            f"""SELECT area FROM `{doc._meta.db_table}` WHERE id = `{word_freq._meta.db_table}`.record_id""",
            ())
        if start_time:
            area_word_freqs = word_freq.objects.filter(
                pub_date__gt=start_time).annotate(record__area=rawsql).values(
                "record__area", "word").annotate(total_freq=Sum("freq")).iterator()
        else:
            area_word_freqs = word_freq.objects.all().annotate(
                record__area=rawsql).values(
                "record__area",
                "word").annotate(total_freq=Sum("freq")).iterator()

    bulk_update_or_create(area_word_freqs, word_freq_aggr)

    total_word_freqs = word_freq_aggr.objects.filter(~Q(area='TOTAL')).values('word').annotate(
        total_freq=Sum('freq')).iterator()
    bulk_update_or_create(total_word_freqs, word_freq_aggr, area_key="TOTAL")
    generate_hotness(data_type=data_type)


@shared_task
def generate_hotness(data_type: int = 1):
    if data_type == 1:
        wordfreq = GovDocWordFreq
        wordfreq_aggr = GovDocWordFreqAggr
    elif data_type == 3:
        wordfreq = ToutiaoDocWordFreq
        wordfreq_aggr = ToutiaoDocWordFreqAggr
    else:
        return None
    top_10_records = wordfreq_aggr.objects.filter(area='TOTAL').order_by('-freq')[:10].iterator()
    hot_list = [i.word for i in top_10_records]
    end_year = datetime.datetime.now().year
    start_year = end_year - 10

    for year in range(start_year, end_year + 1):
        start_date = datetime.datetime(year, 1, 1)
        end_date = datetime.datetime(year + 1, 1, 1) - datetime.timedelta(days=1)

        yearly_word_freqs = (
            wordfreq.objects.filter(word__in=hot_list, pub_date__range=(start_date, end_date))
            .values('word').annotate(yearly_freq=Sum('freq')))

        with transaction.atomic():
            for item in yearly_word_freqs:
                word = item['word']
                yearly_freq = item['yearly_freq']
                yearly_word_freq, created = WordHotness.objects.get_or_create(word=word, year=year,
                                                                              datatype_id=data_type)
                yearly_word_freq.freq = yearly_freq
                yearly_word_freq.save()
        print(f"year{year} done!")


@shared_task
def test_celery_task(testarg1, testarg2, *args):
    logger.info("test celery task")
    logger.info(testarg1)
    logger.info(testarg2)
    logger.info(args)
    logger.info(datetime.datetime.now())
    with open('test.txt', 'a') as f:
        f.write(f"{testarg1} {testarg2} {args} {datetime.datetime.now()}\n")
