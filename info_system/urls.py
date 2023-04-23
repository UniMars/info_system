"""info_system URL Configuration

'urlpatterns' 列表将 URL 路由到视图。详细信息请查看：
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
示例:
函数视图
    1. 导入：from my_app import views
    2. 添加 URL： path('', views.home, name='home')
基于类的视图
    1. 导入：from other_app.views import Home
    2. 添加 URL： path('', Home.as_view(), name='home')
包含另一个 URL 配置文件
    1. 导入 include() 函数：from django.urls import include, path
    2. 添加 URL： path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
                path('', include('home.urls')),
                path('report/', include('report.urls')),
                path('datas/', include('datas.urls')),
                path("admin/", admin.site.urls),
                re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT, }),
            ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
