from django.urls import path

import datas.tasks
from . import views

urlpatterns = [
    # path('', views.index, name='index'),
    path('<int:data_id>', views.index, name='index'),
    path('<int:data_id>/handle_task', datas.views.handle_task_request, name='handle_task'),
    path('<int:data_id>/updateTable', views.table_update, name='updateTable'),
    path('<int:data_id>/wordCloud', views.wordcloud, name="wordcloud"),
    path('<int:data_id>/wordHotness', views.get_word_hotness, name="wordHotness"),
]
