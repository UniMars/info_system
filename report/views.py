from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from pyecharts.charts import Tab

from report.utils.draw_bar_line import draw_bar_line
from report.utils.draw_geo_heatmap import draw_geo_heatmap
from report.utils.draw_radar import draw_radar


# from django.http import HttpResponse


# Create your views here.

def index(response):
    # return
    return render(response, template_name='reports/report.html')


def graph_index(response):
    return render(response, template_name='reports/graph.html')


@csrf_exempt
@cache_page(7200)
def generate_graph(request):
    if request.method == 'POST':
        selected_option = request.POST.get('options')

        # 分离参数
        file_path, name_list_str, page_number_str = selected_option.split(' ')
        file_path = settings.BASE_DIR / "DATA" / file_path
        name_list = eval(name_list_str)
        page_number = int(page_number_str)

        # 调用画图函数，传递参数
        overlap_bar_line = draw_bar_line(file_path=file_path, name_list=name_list, page_number=page_number)
        overlap_radar = draw_radar(file_path=file_path, name_list=name_list, page_number=page_number)
        overlap_geo_heatmap = draw_geo_heatmap(file_path=file_path, name_list=name_list, page_number=page_number)

        # 多张图表分页
        tab = Tab()
        tab.add(overlap_bar_line, "各省份{}可视化".format(name_list[-1]))
        tab.add(overlap_radar, "三大经济区{}可视化".format(name_list[-1]))
        tab.add(overlap_geo_heatmap, "全国{}GEO热力图".format(name_list[-1]))

        chart_html = tab.render_embed()
        chart_html = chart_html.replace(
            """<script type="text/javascript" src="https://assets.pyecharts.org/assets/v5/echarts.min.js"></script>""",
            "")
        chart_html = chart_html.replace(
            """<script type="text/javascript" src="https://assets.pyecharts.org/assets/v5/maps/china.js"></script>""",
            "")
        # 将图表渲染为HTML模板，然后返回给用户的浏览器
        return JsonResponse({'chart': chart_html})
    else:
        return JsonResponse({'chart': 'error'})
