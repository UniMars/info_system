from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('import', views.data_import, name='import'),
    path('updateTable', views.table_update, name='updateTable'),
]
