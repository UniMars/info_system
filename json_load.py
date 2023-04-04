# import xlrd
import csv
import datetime
import json
import os
from datetime import date, datetime

import numpy as np
import pandas as pd
import chardet


class LoadDatetime(json.JSONEncoder):
    """
    重写json的编码器，使其能够将datetime类型的数据转换为字符串
    """

    def default(self, obj):
        if isinstance(obj, datetime):
            try:
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            except Exception as _:
                print(_)
                print(obj)
                return None
        elif isinstance(obj, date):
            try:
                return obj.strftime('%Y-%m-%d')
            except Exception as _:
                print(_)
                print(obj)
                return None
        else:
            return json.JSONEncoder.default(self, obj)


def convert_res(res_list: list):
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
            d[header[i].strip()] = res_list[j + 1][i].strip()
        res_dict.append(d)
    return res_dict


def test(path=r'./DATA/政府网站数据/数据汇总'):
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
                result_dict = convert_res(result)
                res[file.split(".csv")[0]] = result_dict

            elif dir_str.endswith(".xlsx") or dir_str.endswith(".xls"):
                print(dir_str)
                data = pd.read_excel(dir_str)
                result = [data.columns.values.tolist()] + np.array(data).tolist()
                result_dict = convert_res(result)
                res[file.split(".xls")[0]] = result_dict

# print("生成json文件中")
# with open("D:/zl/res_数据汇总.json", "w") as f:
#     json.dump(res, f, cls=LoadDatetime)
# print("Done!")
