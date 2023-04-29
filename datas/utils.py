import logging
import os
import re

import pandas as pd
from django.conf import settings

logger = logging.getLogger('django')


def get_stopwords():
    stop_pattern = re.compile(r'[\s\u2002\u2003\u3000\u200b\u200c\u200d\u206c\xa0\x7f\d二三四五六七八九.]')
    stopwords = set()
    stopwords_file_path = os.path.join(settings.STATIC_ROOT, 'stopwords.txt')
    with open(stopwords_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            stopwords.add(line.strip())
    return stopwords, stop_pattern


def get_gov_doc_name(name_key):
    area_pattern = re.compile(r'[^\d-]+')
    logger.debug(f"读取文件：{name_key}")
    # 匹配地区名
    match_res = area_pattern.search(name_key)
    if match_res and match_res.group()[-2:] == "文件":
        area = match_res.group()[:-2]
    else:
        logger.error('地区名称读取失败')
        area = ''
        # raise ValueError("地区名称读取失败")
    return area


def unpack_result(item, key_map, result):
    for map_key, map_value in key_map.items():
        alternatives = map_value['alternatives']
        read_type = map_value['read_type']
        if read_type == 'and':
            for alt_key in alternatives:
                if alt_key in item:
                    result[map_key] += str(item[alt_key]) + ' '
        else:
            for alt_key in alternatives:
                if alt_key in item:
                    result[map_key] = str(item[alt_key]) if item[alt_key] else ''
                    break
        result[map_key] = result[map_key].strip()


def convert_date(date_value):
    if date_value:
        timestring = date_value
        temp_date = pd.to_datetime(timestring, errors='coerce')
        if temp_date is pd.NaT:
            temp_date = pd.to_datetime(timestring, format="%Y年%m月%d日", errors='coerce')
        temp_date = temp_date if temp_date is not pd.NaT else None
        date_value = temp_date
    else:
        date_value = None
    return date_value


def read_wrong_result(output_file: str):
    read_uids = []
    failed_read_uids = []  # 记录更新失败的uid
    # 读取result.txt结果，解析为uid的list
    with open(file=output_file, mode='r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        try:
            if not line.strip():
                continue
            if "UID_" in line:
                read_uids.append(int(line.strip()[4:]))
            else:
                read_uids.append(int(line.strip()))
        except Exception as _:
            logger.error(f"READ ERROR:{_}")
            failed_read_uids.append(line.strip())

    if failed_read_uids:
        with open(file=output_file, mode='w', encoding='utf-8') as f:
            f.write('\n'.join(uid for uid in failed_read_uids))
    else:
        with open(file=output_file, mode='w', encoding='utf-8') as f:
            f.write('')
    return read_uids
