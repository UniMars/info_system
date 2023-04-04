# -*- coding: utf-8 -*-
# from datetime import datetime
import json
import re
# import time

import pandas as pd
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from .models import GovAggr


# Create your views here.
def index(response):
    # return
    return render(response, 'dataDemo.html')


def data_import(response, filepath: str = r"D:\Programs\Code\python\data\res_DataGather.json"):
    print("导入数据中\n")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            print('文件打开成功\n')
            data_json = json.load(f)
            area_pattern = re.compile(r'[^\d-]+')
            # time_pattern = re.compile(r'\W*\d{4}年\d+月\d{1,2}日\W*')

            for name_key, value_list in data_json.items():
                print(name_key + '\n')
                # 匹配地区名
                match_res = area_pattern.search(name_key)
                if match_res and match_res.group()[-2:] == "文件":
                    area = match_res.group()
                else:
                    print()
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
                                    result[map_key] = str(item[alt_key])
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

                    types = result['types']
                    link = result['link']
                    title = result['title']
                    content = result['content']
                    pub_date = result['pub_date']
                    source = result['source']
                    level = result['level']

                    if pub_date:
                        data_model = GovAggr(area=area, types=types, link=link, title=title, content=content,
                                             pub_date=pub_date, source=source, level=level)
                    else:
                        data_model = GovAggr(area=area, types=types, link=link, title=title, content=content,
                                             source=source, level=level)

                    data_model.save()
                print("输出结束\n")
                return HttpResponse("写入完成")
    except Exception as e:
        print("ERROR:\n")
        print(e)
        print(response)
    return HttpResponse("数据汇总表写入中")


def table_update(request):
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        # search_value = request.GET.get('search[value]', '')
        print()
        queryset = GovAggr.objects.all().order_by('-pub_date')
        total_records = queryset.count()

        paginator = Paginator(queryset, length)
        page_number = (start // length) + 1
        data = [{'发布日期': obj.pub_date, '地区': obj.area, '标题': obj.title, '链接': obj.link, '正文': obj.content}
                for obj in paginator.get_page(page_number)]
        response = {'draw': draw, 'recordsTotal': total_records, 'recordsFiltered': total_records, 'data': data}
        return JsonResponse(response)
    except Exception as e:
        data = []
        print("ERROR:\n")
        print(request)
        print(e)
        return JsonResponse(data, safe=False)
