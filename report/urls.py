from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # path('graph/', views.graph_index, name='graph'),
    # path('graph/generate_graph', views.generate_graph, name='generate_graph')
]
