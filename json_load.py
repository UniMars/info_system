import os
import pandas as pd
import numpy as np
import json
import datetime
import csv
from datetime import date, datetime


class LoadDatetime(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            try:
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            except:
                print(obj)
                return None
        elif isinstance(obj, date):
            try:
                return obj.strftime('%Y-%m-%d')
            except:
                print(obj)
                return None
        else:
            return json.JSONEncoder.default(self, obj)


res = {}


def convert_res(res):
    res_dict = []
    for j in range(len(res[1:])):
        d = {}
        for i in range(len(res[0])):
            d[res[0][i]] = res[j + 1][i]
        res_dict.append(d)
    return res_dict


for root, dirs, files in os.walk(r"D:\zl\数据汇总"):
    for file in files:
        dir_str = os.path.join(root, file)
        if dir_str.endswith(".csv"):
            try:
                with open(dir_str, "r", encoding="utf-8") as fp:
                    print(dir_str)
                    reader = csv.reader(fp)
                    result = list(reader)
            except:
                with open(dir_str, "r") as fp:
                    print(dir_str)
                    reader = csv.reader(fp)
                    result = list(reader)
            result_dict = convert_res(result)
            res[dir_str.split(".csv")[0].split("\\")[-1]] = result_dict

        elif dir_str.endswith(".xlsx") or dir_str.endswith(".xls"):
            print(dir_str)
            data = pd.read_excel(dir_str)
            result = [data.columns.values.tolist()] + np.array(data).tolist()
            result_dict = convert_res(result)
            res[dir_str.split(".xls")[0].split("\\")[-1]] = result_dict

print("生成json文件中")
with open("D:/zl/res_数据汇总.json", "w") as f:
    json.dump(res, f, cls=LoadDatetime)
print("Done!")