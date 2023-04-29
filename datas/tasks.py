import concurrent.futures
import datetime
import gc
import logging
import multiprocessing
import os
import re
from collections import defaultdict
from typing import Union

import jieba
from celery import shared_task
from django.conf import settings
from django.db import transaction, connections
from django.db.models import Sum

from datas.models import GovDoc, GovDocWordFreq, GovDocWordFreqAggr, ToutiaoDoc, WordHotness
from datas.utils import get_stopwords, get_gov_doc_name, unpack_result, convert_date, read_wrong_result
from utils.json_load import load_forms
from utils.utils import generate_id

# logger = logging.getLogger('django')
logger = logging.getLogger('tasks')


def gov_data_import(filepath: str = ""):
    if not filepath:
        filepath = settings.BASE_DIR / "DATA/政府网站数据/数据汇总"
    logger.info("政府汇总数据导入中")
    logger.info(f"读取文件：{filepath}")
    try:
        data_json = load_forms(filepath)
        # time_pattern = re.compile(r'\W*\d{4}年\d+月\d{1,2}日\W*')

        for name_key, value_list in data_json.items():
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


def toutiao_data_import(rootpath: str = ""):
    if not rootpath:
        rootpath = settings.BASE_DIR / "DATA/头条"
    logger.info("头条数据导入中")
    logger.info(f"读取文件：{rootpath}")
    try:
        data_json = load_forms(rootpath)
        for name_key, value_list in data_json.items():

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
                data_model.save()
    except Exception as e:
        logging.error(f"ERROR:{e}")
        return "error"


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
        # iterator = articles.iterator(chunk_size=articles.count() // cpu_count + 1)
        article_count = articles.count()
        chunk_size = article_count // cpu_count + 1
        chunks = [articles[i:i + chunk_size].iterator() for i in range(0, article_count, chunk_size)]

        thread = 0
        for chunk in chunks:
            logger.debug(f"WORKER {thread} start")
            params = {
                'model_list_iterator': chunk,
                'tokenizer': tokenizer,
                'stopwords': stopwords,
                'stop_pattern': stop_pattern,
                'worker': thread
            }
            future = executor.submit(word_split_multiprocess_task, **params)
            futures.append(future)
            futures_dict[str(thread)] = future
            thread += 1

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
            word_total_models.extend(read_uids)

            # 将uid按每批1000个进行划分
            batch_size = 10000
            uid_batches = [word_total_models[i:i + batch_size] for i in range(0, len(word_total_models), batch_size)]
            failed_uids = []  # 记录更新失败的uid
            for uid_batch in uid_batches:
                word_aggr_updates = defaultdict(lambda: defaultdict(int))
                try:
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
                except Exception as e:
                    logger.error(f"WordFreqAggr Updating:{e}")
                    failed_uids.extend(uid_batch)
                    continue
                else:
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
        logger.info("----------All Thread finished----------")
        return "分词结束"


def word_split_multiprocess_task(model_list_iterator,
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
    gc_count = 0
    try:
        for article in model_list_iterator:
            # 分词并词频统计
            # time1=time.time()
            word_freq = defaultdict(int)
            for word in tokenizer.cut(article.content):
                # 去除停用词和数字,标点符号,并转换为小写
                if word in stopwords or stop_pattern.search(word):
                    continue
                word = word if not word.isalpha() else word.lower()
                # 词频统计
                word_freq[word] += 1
            # time2=time.time()
            # logger.debug(f"ARTICLE: {article.id} jieba cost {time2-time1}")
            # time3=time.time()
            # 保存词频统计结果写入数据表
            word_model_list = []
            for word, freq in word_freq.items():
                uid = generate_id(word, article.id)
                if GovDocWordFreq.objects.filter(id=uid).exists():
                    continue
                else:
                    word_freq_model = GovDocWordFreq(id=uid, word=word, freq=freq, record=article)
                    word_model_list.append(word_freq_model)
                    word_total_models.append(uid)
            # time4 = time.time()
            # logger.debug(f"ARTICLE: {article.id} convert cost {time4 - time3}")
            # time5 = time.time()
            with transaction.atomic():
                if word_model_list:
                    GovDocWordFreq.objects.bulk_create(word_model_list)
                article.is_split = True
                article.save(update_fields=['is_split'])
                # time6 = time.time()
                # logger.debug(f"ARTICLE: {article.id} save cost {time6 - time5}")
                logger.debug(f"article:{article.id} save success with WORKER:{worker}")
            del word_model_list
            del word_freq
    except Exception as e:
        logger.error(f"bulk transaction error:{e} with WORKER:{worker}")
    finally:
        gc_count += 1
        if gc_count == 500:
            gc_count = 0
            gc.collect()
            # 销毁word_model_list
    return word_total_models


def generate_hotness(data_type: int = 1):
    if data_type == 1:
        hot_list = ['发展', '建设', '经济', '企业', '数字', '新', '产业', '创新', '工作', '推进', ]
        wordfreq = GovDocWordFreq
    else:
        return None
    end_year = datetime.datetime.now().year
    start_year = end_year - 10

    for year in range(start_year, end_year + 1):
        start_date = datetime.datetime(year, 1, 1)
        end_date = datetime.datetime(year + 1, 1, 1) - datetime.timedelta(days=1)

        yearly_word_freqs = (
            wordfreq.objects.filter(word__in=hot_list, area="TOTAL", pub_date__range=(start_date, end_date))
            .values('word').annotate(yearly_freq=Sum('freq')))

        with transaction.atomic():
            for item in yearly_word_freqs:
                word = item['word']
                yearly_freq = item['yearly_freq']
                yearly_word_freq, created = WordHotness.objects.get_or_create(word=word, year=year)
                yearly_word_freq.freq = yearly_freq
                yearly_word_freq.save()
        print(f"year{year} done!")


@shared_task
def test_celery_task():
    logger.info("test celery task")
    logger.info(datetime.datetime.now())
