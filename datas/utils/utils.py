import hashlib
import logging
import os
import re

import pandas as pd
from django.conf import settings

logger = logging.getLogger('tasks')
TIME_PATTERNS = [
    re.compile(r'((\d{2}|\d{4})[-/\\.])?\d{1,2}[-/\\.]\d{1,2}(\s*[Tt]?\d{1,2}:\d{1,2}(:\d{1,2})?(\s*(am|AM|pm|PM))?)?'),
    re.compile(r'\d{1,2}[-/\\.]\d{1,2}[-/\\.](\d{2}|\d{4})(\s*[Tt]?\d{1,2}:\d{1,2}(:\d{1,2})?(\s*(am|AM|pm|PM))?)?'),
    re.compile(
        r'((\d{2}|\d{4})[-/\\年.])?\d{1,2}[-/\\月.]\d{1,2}日?(\s*(下午|上午)?\d{1,2}[:点时]\d{1,2}([:分]\d{1,2}秒?)?)?'),
]


def generate_id(word: str, record_id: int):
    # 使用哈希函数（如SHA-256）计算word的哈希值
    hash_obj = hashlib.sha256(word.encode())
    hash_value = int(hash_obj.hexdigest(), 16)

    # 取哈希值的低32位
    hash_lower_32_bits = hash_value & 0xFFFFFFFF

    # 将哈希值与record_id组合以生成64位ID
    id_64_bits = (hash_lower_32_bits << 32) | record_id

    # 将最高位设置为0，以确保返回的是63位整数
    id_63_bits = id_64_bits & 0x7FFFFFFFFFFFFFFF

    return id_63_bits


def data_cleaning(content):
    content = re.sub('[\u2002\u2003\u3000\u200b\u200c\u200d\u206c\xa0\x7f]', ' ', content)
    content = content.replace('\xad', '')
    content = content.strip()
    return content


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
        timestring = date_value.strip()
        raw_time_string = timestring
        temp_date = pd.to_datetime(timestring, errors='coerce')
        if temp_date is not pd.NaT:
            return temp_date
        for time_pattern in TIME_PATTERNS:
            if time_pattern.search(timestring):
                timestring = time_pattern.search(timestring).group()
                timestring = timestring.replace('年', '-').replace('月', '-').replace('日', '')
                timestring = timestring.replace('时', ':').replace('分', ':').replace('秒', '').replace('点', ':')
                if "上午" in timestring:
                    timestring = timestring.replace("上午", "") + " AM"
                elif "下午" in timestring:
                    timestring = timestring.replace("下午", "") + " PM"
                break
        temp_date = pd.to_datetime(timestring, errors='coerce')

        if temp_date is not pd.NaT:
            return temp_date
        else:
            with open(settings.BASE_DIR / 'error_date.txt', 'a', encoding='utf-8') as f:
                f.write(f"{raw_time_string}\n")
            return None
    else:
        return None


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
