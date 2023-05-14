# _*_ coding :utf-8 _*_
# @Time : 2023/4/25 14:58
# @Author ：李文杰
from django.core.cache import cache
from pyecharts import options as opts
# 导入必要的库
from pyecharts.charts import Geo

from .read_file_to_dataframe import read_file_to_dataframe


# @cache_page(7200)
def draw_geo_heatmap(file_path, name_list, page_number=0):
    """
       :param file_path: 数据文件路径
       :param name_list: 画图所需列名列表，格式为["地区",{次级指标},{指标}]
       :param page_number: 若表内有多个附表，输入表序号（从0开始），默认单表
       :return:画图对象geo
       """

    # 读取数据
    df = cache.get(f'index_{page_number}_df')
    print(df)
    if df is None:
        df = read_file_to_dataframe(file_path, page_number)
        cache.set(f'index_{page_number}_df', df, timeout=7200)
    df = df[name_list]

    # 构造（"地区"，"指数"）列表
    para_list = []

    for i in df.index:
        # 修改名称不一致地区
        if df.loc[i, name_list[0]] == "广西壮族自治区":
            df.loc[i, name_list[0]] = "广西"
        elif df.loc[i, name_list[0]] == "西藏自治区":
            df.loc[i, name_list[0]] = "西藏"
        elif df.loc[i, name_list[0]] == "新疆维吾尔自治区":
            df.loc[i, name_list[0]] = "新疆"

        # [0,1]的指标放大到[0,100]
        if df.loc[i, name_list[-1]] < 1:
            df.loc[i, name_list[-1]] = df.loc[i, name_list[-1]] * 100

        # 生成(地区，数据)元组
        t = (df.loc[i, name_list[0]], df.loc[i, name_list[-1]])

        # 添加到参数链表
        para_list.append(t)

    # GEO地理图表绘制
    geo = Geo(init_opts=opts.InitOpts(theme='light',
                                      width='1000px',
                                      height='600px'))
    geo.add_schema(maptype="china")

    # 数据点为热力图模式
    geo.add("", para_list, type_='heatmap')

    # 热点图必须配置visualmap_opts
    geo.set_global_opts(visualmap_opts=opts.VisualMapOpts(pos_top="middle"),
                        title_opts=opts.TitleOpts(title="全国{}GEO热力图".format(name_list[-1])),
                        tooltip_opts=opts.TooltipOpts(is_show=False))

    # 返回画图对象
    return geo


# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    # 调试语句
    chart = draw_geo_heatmap("../数字经济数据汇总.xlsx",
                             ["地区", "互联网基础设施", "政府数据开放", "新型基础设施", "基础设施指数"], 0)
    chart.render("Geo.html")
