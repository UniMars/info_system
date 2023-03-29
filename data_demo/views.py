# -*- coding: utf-8 -*-
from datetime import datetime
import json
import re
import time

import pandas as pd
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from .models import DataAggr


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
            time_pattern = re.compile(r'\W*\d{4}年\d+月\d{1,2}日\W*')
            for key, value in data_json.items():
                print(key)
                print()
                match_res = area_pattern.search(key)
                if match_res and match_res.group()[-2:] == "文件":
                    area = match_res.group()
                else:
                    print()
                    raise ValueError("地区名称读取失败")
                for item in value:

                    if 'type' in item:
                        types = str(item['type'])
                    elif '新闻类型' in item:
                        types = str(item['新闻类型'])
                    else:
                        types = ''
                        # raise ValueError("types读取失败")
                    # print(1)

                    if 'link' in item:
                        link = str(item['link'])
                    elif '链接' in item:
                        link = str(item['链接'])
                    else:
                        link = ''
                        # raise ValueError("link读取失败")
                    # print(2)

                    if 'title' in item:
                        title = str(item['title'])
                    elif '标题' in item:
                        title = str(item['标题'])
                    else:
                        title = ''
                        # raise ValueError("title读取失败")
                    # print(3)

                    if '正文内容' in item:
                        content = str(item['正文内容'])
                    # elif '链接' in item:
                    #     link = item['链接']
                    else:
                        content = ''
                        # raise ValueError("content读取失败")
                    # print(4)

                    # print(item['发布日期'])
                    if '发布日期' in item and item['发布日期']:
                        timestring = item['发布日期']
                        if time_pattern.fullmatch(timestring):
                            pub_date = pd.to_datetime(timestring, format="%Y年%m月%d日")
                        else:
                            pub_date = pd.to_datetime(timestring)

                    else:
                        pub_date = None
                        # raise ValueError("日期读取失败")
                    # print(5)

                    if 'department' in item:
                        department = item['department']
                    elif '来源' in item:
                        department = item['来源']
                    else:
                        department = ''
                        # raise ValueError("department 读取失败")
                    # print(6)

                    if '级别' in item:
                        level = item['级别']
                        # elif '链接' in item:
                        #     link = item['链接']
                    else:
                        level = ''
                        # raise ValueError("level 读取失败")
                    # print(7)

                    if '类别' in item:
                        cate = item['类别']
                    elif '文件类型' in item:
                        cate = item['文件类型']
                    else:
                        cate = ''
                        # raise ValueError("cate 读取失败")
                    # print(8)

                    if pub_date:
                        data_model = DataAggr(area=area, types=types, link=link, title=title, content=content,
                                              pub_date=pub_date, department=department, level=level, cate=cate)
                    else:
                        data_model = DataAggr(area=area, types=types, link=link, title=title, content=content,
                                              department=department, level=level, cate=cate)

                    data_model.save()
                print("输出结束\n")
                return HttpResponse("写入完成")
    except Exception as e:
        print("ERROR:\n")
        print(response)
        print(e)
    return HttpResponse("数据汇总表写入中")


def table_update(request):
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        print()
        queryset = DataAggr.objects.all().order_by('pub_date')
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
