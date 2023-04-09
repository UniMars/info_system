from django.urls import path

import datas.tasks
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # path('import', datas.tasks.gov_data_import, name='import'),
    path('handle_task', datas.views.handle_task_request, name='handle_task'),
    path('updateTable', views.table_update, name='updateTable'),
    # path('wordSplit', datas.tasks.word_split, name='wordSplit'),
    path('wordCloud', views.wordcloud, name="wordcloud")
]
