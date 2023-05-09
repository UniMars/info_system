# _*_ coding :utf-8 _*_
# @Time : 2023/4/15 19:37
# @Author ：李文杰
# 导入画图所需要的包
from pyecharts import options as opts
from pyecharts.charts import Bar, Line

from .read_file_to_dataframe import read_file_to_dataframe


# @cache_page(7200)
def draw_bar_line(file_path, name_list, page_number=0):
    """
    :param file_path: 数据文件路径
    :param name_list: 画图所需列名列表，格式为["地区",{次级指标},{指标}]，
                    "地区"为x轴，{次级指标}为bar的y轴，指标为Line的y轴
    :param page_number: 若表内有多个附表，输入表序号（从0开始），默认单表
    :return:返回画图对象overlap
    """

    # 读取数据
    df = read_file_to_dataframe(file_path, page_number)
    df = df[name_list]

    # 分别获取X轴和Y轴数据
    n_cols = len(df.columns)
    x_data = df.iloc[:, 0]
    y_data = df.iloc[:, 1:n_cols]

    # “次级指标”作为Y轴，“地区”作为X轴，绘制柱状图
    bar = Bar(init_opts=opts.InitOpts(theme='white', width='1000px', height='600px'))
    for i, col in enumerate(y_data.columns[:-1]):
        bar.add_xaxis(x_data.tolist())
        bar.add_yaxis(col, y_data.iloc[:, i].tolist(), category_gap=0, label_opts=opts.LabelOpts(is_show=False))
    bar.set_global_opts(
        title_opts=opts.TitleOpts(title=name_list[-1]),
        xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=90, font_size=10)),
        tooltip_opts=opts.TooltipOpts(is_show=True,
                                      # 提示框背景颜色
                                      background_color="white")
    )

    # 将最后一列数据作为Y轴，第一列数据作为X轴，绘制折线图
    line = Line()
    line.add_xaxis(x_data.tolist())
    # 将指标数据归一化到[0,1]之间，方便与柱状图展示在同一张图中
    if df.iloc[1, -1] > 1:
        line.add_yaxis(name_list[-1], df.iloc[:, -1].div(100).tolist(), label_opts=opts.LabelOpts(is_show=False))
    else:
        line.add_yaxis(name_list[-1], df.iloc[:, -1].tolist(), label_opts=opts.LabelOpts(is_show=False))
    line.set_global_opts(title_opts=opts.TitleOpts(title=name_list[-1]))

    # 使折线图层叠在柱状图的上方
    line.set_series_opts(z=2)

    # 将两个图表合并为一个，显示出来
    overlap = bar.overlap(line)

    # # 调试输出语句
    # overlap.render("{}_bar_line.html".format(name_list[-1]))

    return overlap


# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    # 调试语句
    draw_bar_line(file_path="../数字经济数据汇总.xlsx",
                  name_list=["地区", "基础设施指数", "数字产业发展指数", "产业融合指数", "发展环境指数",
                                          "数字经济发展指数"], page_number=4)
