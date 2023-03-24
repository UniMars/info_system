from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('current_time', views.current_time)
]
