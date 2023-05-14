from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('getDocSum', views.get_doc_sum, name='get_doc_sum'),
]
