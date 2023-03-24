# -*- coding: utf-8 -*-
# import datetime
import json
import re

# import pandas as pd

# a=datetime.datetime.now()
print()
a = r"D:\Programs\Code\python\data\res_31_prov_data.json"
b = r"D:\Programs\Code\python\data\res_DataGather.json"
c = r"D:\Programs\Code\python\data\original\res_数据汇总.json"
try:
    with open(c, 'r', encoding='utf-8') as f:
        bb = json.load(f)
        area_pattern = re.compile(r'[^\d-]+')
        area = ""
        for key, value in bb.items():
            match_res = area_pattern.search(key)
            if match_res and match_res.group()[-2:] == "文件":
                area = match_res.group()
            else:
                raise ValueError("地区名称读取失败")
            # for item in value:

            print()
except Exception as e:
    print(e)
# fp1='data/res_DataGather.json'
# fp2='data/res_31_prov_data.json'
# fp3='data/res_头条新闻.json'
# for i in [fp1,fp2,fp3]:
#     with open(i,'r')as f:
#         a=json.load(f)
#         with open(i+".json",'w',encoding='utf-8') as outf:
#             json.dump(a, outf,ensure_ascii=False)
#         print(i)
