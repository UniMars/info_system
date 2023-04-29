# -*- coding: utf-8 -*-
import datetime
import json
import os.path
import random
import re
import time
import traceback
import urllib
from urllib import request as urllib2
# import string
from urllib.parse import quote

import openpyxl as op
import xlwt
from bs4 import BeautifulSoup
from datas.utils.utils import data_cleaning
from django.conf import settings
from selenium import webdriver
from selenium.webdriver.common.by import By

start_time = time.time()
keyword = '数字经济'


def toutiao_spider(area_keyword, search_keyword):
    for j in range(18):  # 今日头条搜索资讯一栏大概每个关键词会弹出18页
        file_name = '今日头条+' + area_keyword + '.xlsx'
        root_path = settings.BASE_DIR / 'DATA/头条'
        file_path = root_path / file_name
        try:
            wb = op.load_workbook(file_path)  # 该文件需要提前创建
        except FileNotFoundError:
            if not os.path.exists(root_path):
                os.makedirs(root_path)
            wb = op.Workbook()
            sh = wb.worksheets[0]
            sh.append(['title', 'url', 'area_keyword', 'search_keyword', 'date', 'media', 'context', 'comment'])
            wb.save(file_path)
            wb = op.load_workbook(file_path)
        finally:
            ws = wb.worksheets[0]
        driver = webdriver.Chrome(executable_path="D:/ProgramData/selenium/chromedriver.exe")
        try:  # 为了防止某搜索页面没有18页或者第18页没有10个资讯而报错
            url = 'https://so.toutiao.com/search?keyword=' + quote(area_keyword) + '%20' + quote(search_keyword) \
                  + '&pd=information&source=search_subtab_switch&dvpf=pc&aid=4916&page_num=' + str(j)  # url链接
            driver.get(url)
            time.sleep(1.25)  # 可根据实际情况调整
            for i in range(1, 11):  # 每一页有10篇文章
                link = driver.find_element(By.XPATH,
                                           '/html/body/div[2]/div[2]/div[{}]/div/div/div/div/div[1]/div/a'.format(
                                               str(i)))
                url = link.get_attribute('href')  # 定位文章的链接
                driver.get(url)  # 获取具体的文章页面
                time.sleep(0.75)
                tdmc = driver.find_element(By.CLASS_NAME, 'article-content').text
                list1 = tdmc.split('\n', 2)
                title = list1[0].strip()
                date = list1[1].split('·')[0]
                media = list1[1].split('·')[1].strip()
                context = data_cleaning(list1[2])
                # 解析网页获取文章的题目、时间、来源、正文、部分评论
                comment = driver.find_element(By.CLASS_NAME, 'comment-list').text
                comment = data_cleaning(comment)
                ws.append([title, url, area_keyword, search_keyword, date, media, context, comment])
                wb.save(file_path)  # 保存文件
                driver.back()  # 退回搜索文章的页面
                time.sleep(1)
            print(datetime.datetime.now(), ':已爬取到关键词:', search_keyword, "的第", j + 1, '页')  # 查看爬取进度
        except Exception as _:
            print(_)
        driver.close()
    end_time = time.time()
    print(end_time - start_time)


class WeiboContent:
    """
    @author: 李梓琪
    注意事项：
    1、更换cookie和agents序列
    2、程序入口处可选择需要的关键词列表和省份
    3、默认从话题第一页开始爬取，有需要可以更改页数
    4、最终print的dic1，会显示各个关键词爬取的最终页数。部分爬取过程中超时报错的，可以从显示的最终页数开始重新爬取。
    5、其他见代码注释。
    """

    # 爬取代码
    @staticmethod
    def read_html(key, page):  # 关键词，从话题第几页开始爬取
        info_list = []
        try:
            info_list = []  # 存储所有微博的数据

            my_agents = ["", "", "", "", ""]  # 设置一系列代理，通过random函数更换代理，减少反爬屏蔽
            randdom_agents = random.choice(my_agents)
            cookies = ''
            headers = {'User-Agent': randdom_agents, 'cookie': cookies}

            key_word = urllib.parse.quote(key)  # 将关键词转化为url格式

            while page:  # 爬取每一页的数据
                flag = 0  # 等于1时跳出循环

                if page == 1:  # 第一页和其他话题页url有些许区别。爬取的是网页端实时微博下拉加载页，数据格式为键值对。可根据需要爬取的页面替换url。
                    url = 'https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D61%26q%3D{0}%26t%3D0&page_type=searchall'.format(
                        key_word)
                else:
                    url = 'https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D61%26q%3D{0}%26t%3D0&page_type=searchall&page={1}'.format(
                        key_word, page)

                request = urllib2.Request(url=url, headers=headers)
                req = urllib2.urlopen(request, timeout=10)  # 发送请求
                index_doc = req.read()  # 读取页面内容
                index_json = json.loads(index_doc)  # 使用json.loads()将获取的返回内容转换成json格式

                cards = index_json['data']['cards']  # 微博数据集。如需爬取综合排序、热门微博等数据，需要根据具体数据层级来获得微博数据集。
                start = 0
                end = len(cards)  # 该页面微博数量
                if end == 0:  # 该页面无数据，数据爬取结束，跳出循环
                    print('no more data')
                    break
                for i in range(start, end):
                    mblog_url = cards[i]['scheme']  # 该页面第i-1条微博的地址
                    mblog = cards[i]['mblog']  # 该页面第i-1条微博

                    if 'retweeted_status' in mblog:  # 跳过转发的微博。需要保留可删除本条。
                        print('no content {0}'.format(i))
                        continue

                    reposts_count = mblog['reposts_count']  # 转发数量
                    comments_count = mblog['comments_count']  # 评论数量
                    attitudes_count = mblog['attitudes_count']  # 点赞数量

                    date = mblog['created_at']  # 发表时间
                    month = date[4:7]  # 从时间中提取月份
                    year = date[-4:]  # 从时间中提取年份
                    if '2019' in date or '2018' in date:  # 只爬取2020及以后的数据，所以出现19、18年的数据就跳出循环，停止爬取数据
                        flag = 1
                        break

                    mid = mblog['id']  # 微博ID
                    pic_num = mblog['pic_num']  # 微博带图数量

                    long_text = mblog['isLongText']  # 判断是否为长微博，如果是的话需要进行处理
                    if long_text:
                        text_id = mblog['id']  # 微博ID
                        text_href = 'https://m.weibo.cn/statuses/extend?id={0}'.format(
                            text_id)  # 长微博地址
                        text_req = urllib2.Request(url=text_href, headers=headers)
                        text_doc = urllib2.urlopen(text_req, timeout=10).read()  # 读取长微博数据
                        text_json = json.loads(text_doc)  # 转换为json格式
                        text = text_json['data']['longTextContent']  # 长微博文本数据
                    text = mblog['text']  # 微博文本数据
                    length = mblog['textLength']  # 微博文本长度
                    text_soup = BeautifulSoup(text, "html.parser")  # 对文本数据进行处理，转化为txt格式
                    content = text_soup.get_text()  # txt文本
                    urls = len(re.findall('small_web_default.png', text)) + len(
                        re.findall('small_article_default.png', text))  # 文本中超链接数量

                    source = mblog['source']  # 微博数据来源

                    is_location = len(re.findall('small_location_default.png', text))  # 微博是否带有定位信息
                    if is_location:
                        location = text_soup.find_all("span", {"class": "surl-text"})[-1].get_text()  # 定位
                    else:
                        location = ''

                    # 提取用户信息
                    user = mblog['user']  # 用户数据
                    user_id = user['id']
                    user_name = user['screen_name']
                    user_gender = user['gender']
                    user_statuses_count = user['statuses_count']  # 发博总数
                    user_followers_count = user['followers_count']  # 粉丝数
                    user_follow_count = user['follow_count']  # 关注数
                    user_verified = user['verified']  # 微博是否认证
                    user_verified_type = user['verified_type']  # 微博认证类型，-1普通用户 0名人 1政府 2企业 3媒体 4校园
                    if 'verified_reason' in user:
                        user_verified_reason = user['verified_reason']  # 认证原因
                    else:
                        user_verified_reason = ''
                    user_urank = user['urank']  # 微博等级

                    if 'page_info' in mblog:  # 是否链接其他页面
                        page_info = mblog['page_info']
                        is_splmt = 1
                        splmt_type = page_info['type']  # 视频、直播、网页、股票等
                        splmt_title = page_info["page_title"]
                        splmt_url = page_info["page_url"]
                    else:
                        is_splmt = 0
                        splmt_type = ""
                        splmt_title = ""
                        splmt_url = ""

                    # 单条微博的信息
                    info = (year, month, mblog_url, mid, user_id, user_name, source, user_gender, user_statuses_count,
                            user_followers_count, user_follow_count,
                            user_verified, user_verified_type, user_verified_reason, user_urank, location, content,
                            length, is_splmt, splmt_type, splmt_title, splmt_url, urls,
                            reposts_count, comments_count, attitudes_count, pic_num)
                    info_list.append(info)
                    print('card {0} fin'.format(i))
                print('get page:%d' % page)

                page += 1  # 爬取下一页数据
                year.sleep(2 * random.random())  # 停两秒，反爬
                if flag == 1:
                    print('datas needed are completed')
                    break
            return info_list, page
        except Exception as _:
            traceback.print_exc()
            return info_list, page

    # 存入excel
    def save_excel(self, key="", page=1):  # 关键词，从话题第几页开始爬取
        info_list, page2 = self.read_html(key, page)  # 返回爬取的数据和页面
        file = xlwt.Workbook()
        sh = file.add_sheet(u'Sheet', cell_overwrite_ok=True)
        sh.col(2).width = 50 * 80
        sh.col(21).width = 50 * 80
        sh.col(16).width = 256 * 80
        style = xlwt.easyxf('align: wrap on, vert centre, horiz center')  # 设置显示格式

        row0 = (
            'time', 'month', 'mblogurl', 'mid', 'user_id', 'user_name', 'source', 'user_gender', 'user_statuses_count',
            'user_followers_count', 'user_follow_count', 'user_verified', 'user_verified_type', 'user_verified_reason',
            'user_urank',
            'location', 'content', 'length', 'is_splmt', 'splmt_type', 'splmt_title', 'splmt_url', 'urls_num',
            'reposts_count', 'comments_count', 'attitudes_count', 'pic_num')
        for i in range(0, len(row0)):  # 写入第一行标题
            sh.write(0, i, row0[i], style)

        for i in range(0, len(info_list)):  # 将info_list中的微博逐行写入
            for j in range(0, len(info_list[i])):
                sh.write(i + 1, j, info_list[i][j], style)

        file.save('D:/北京/{0}.xls'.format(key))  # 保存文件
        print('save success')
        return page2
