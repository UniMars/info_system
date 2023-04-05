from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('import', views.data_import, name='import'),
    path('updateTable', views.table_update, name='updateTable'),
    path('wordSplit', views.word_split, name='wordSplit'),
    path('wordCloud', views.wordcloud, name="wordcloud")
]
