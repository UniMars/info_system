# _*_ coding :utf-8 _*_
# @Time : 2023/4/15 22:50
# @Author ：李文杰
import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Radar

from .read_file_to_dataframe import read_file_to_dataframe


# @cache_page(7200)
def draw_radar(file_path, name_list, page_number=0):
    """
    :param file_path: 数据文件路径
    :param name_list: 画图所需列名列表，格式为["地区",{次级指标},{指标}]，
                    "地区"为x轴，{次级指标}画bar，指标画Line
    :param page_number: 若表内有多个附表，输入表序号（从0开始），默认单表
    :return:返回画图对象overlap
    """

    # 读取数据
    df = read_file_to_dataframe(file_path, page_number)
    df = df[name_list]

    # 设置地区为索引
    df = df.set_index('地区')  # 将第一列设置为索引

    # 构建三个经济圈数据
    df_area = pd.DataFrame(columns=df.columns, index=["京津冀", "长三角", "珠三角"])

    # 三个经济圈包含省份list
    region_jjj = ["北京市", "天津市", "河北省"]
    region_csj = ["上海市", "江苏省", "浙江省", "安徽省"]
    region_zsj = ["广东省"]

    # 以包含省份数据平均值作为经济圈数据
    df_area.loc["京津冀"] = df.loc[region_jjj, :].mean()
    df_area.loc["长三角"] = df.loc[region_csj, :].mean()
    df_area.loc["珠三角"] = df.loc[region_zsj, :].mean()

    # 雷达图绘制
    radar = Radar(init_opts=opts.InitOpts(theme="white", width='1000px', height='600px'))

    # 构建坐标轴
    indicator_list = []
    for c in df_area.columns:
        if df_area[c].max() > 1:
            max_value = 100
        else:
            max_value = 1
        indicator_list.append(opts.RadarIndicatorItem(name=c, max_=max_value))

    # 添加坐标轴
    radar.add_schema(indicator_list, textstyle_opts=opts.TextStyleOpts(color="black"))

    # 设置颜色列表
    color_list = ['#5470C6', '#91CC75', '#FACB58']

    # 经济圈数据为变量
    for i in range(3):
        radar.add(
            df_area.index[i],
            [df_area.iloc[i, :].tolist()],
            linestyle_opts=opts.LineStyleOpts(width=2, color=color_list[i]),
            # 添加雷达图线条样式配置
            # 设置标签字体大小
            label_opts=opts.LabelOpts(font_size=12, is_show=False, color=color_list[i]),

        )

    # 全局配置
    radar.set_global_opts(
        title_opts=opts.TitleOpts(title="三大经济区{}分析".format(name_list[-1])), legend_opts=opts.LegendOpts()
    )

    # 调试输出用
    # radar.render("{}_radar.html".format(name_list[-1]))

    return radar


# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    # 调试语句
    draw_radar(file_path="../数字经济数据汇总.xlsx",
               name_list=["地区", "基础设施指数", "数字产业发展指数", "产业融合指数", "发展环境指数",
                                    "数字经济发展指数"], page_number=4)
