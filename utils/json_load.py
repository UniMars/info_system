import csv
import datetime
import hashlib
import json
import os
import re
import shutil
from datetime import date, datetime

import chardet
import numpy as np
import pandas as pd


# class LoadDatetime(json.JSONEncoder):
#     """
#     重写json的编码器，使其能够将datetime类型的数据转换为字符串
#     """
#
#     def default(self, obj):
#         if isinstance(obj, datetime):
#             try:
#                 return obj.strftime('%Y-%m-%d %H:%M:%S')
#             except Exception as _:
#                 print(_)
#                 print(obj)
#                 return None
#         elif isinstance(obj, date):
#             try:
#                 return obj.strftime('%Y-%m-%d')
#             except Exception as _:
#                 print(_)
#                 print(obj)
#                 return None
#         else:
#             return json.JSONEncoder.default(self, obj)


def convert_std_table(res_list: list):
    """
    将csv文件读取的结果转换为字典
    :param res_list: 一个包含若干个嵌套列表的列表，其中第一个列表包含表头，随后列表包含具体数据
    :return: 一个包含若干个字典的列表，其中每个字典的键为表头，值为具体数据
    """
    res_dict = []
    header = res_list[0]
    for j in range(len(res_list[1:])):
        d = {}
        for i in range(len(header)):
            content = res_list[j + 1][i]
            # content 类型判断和清洗
            if isinstance(content, str):
                content = re.sub('[\u2002\u2003\u3000\xa0]', ' ', content)
                content = content.strip()
            try:
                d[header[i].strip()] = content
            except Exception as _:
                print(_)
        res_dict.append(d)
    return res_dict


def load_forms(path: str, if_move=False):
    res = {}
    for root, dirs, files in os.walk(path):
        for file in files:
            dir_str = os.path.join(root, file)
            if dir_str.endswith(".csv"):
                try:
                    with open(dir_str, 'rb') as _:
                        encoding = chardet.detect(_.read())['encoding']
                    with open(dir_str, "r", encoding=encoding) as fp:
                        print(dir_str)
                        reader = csv.reader(fp)
                        result = list(reader)
                except Exception as e:
                    print(e)
                result_dict = convert_std_table(result)
                res[file.split(".csv")[0]] = result_dict

            elif dir_str.endswith(".xlsx") or dir_str.endswith(".xls"):
                print(dir_str)
                data = pd.read_excel(dir_str)
                result = [data.columns.values.tolist()] + np.array(data).tolist()
                result_dict = convert_std_table(result)
                res[file.split(".xls")[0]] = result_dict

            # move file to move_path
            if if_move:
                move_path = os.path.join(root, '/processed')
                if not os.path.exists(move_path):
                    os.makedirs(move_path)
                shutil.move(os.path.join(root, file), move_path)
    return res


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

# print("生成json文件中")
# with open("D:/zl/res_数据汇总.json", "w") as f:
#     json.dump(res, f, cls=LoadDatetime)
# print("Done!")
# test()
