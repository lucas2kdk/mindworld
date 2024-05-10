from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('nodes/', views.dashboard_nodes, name='dashboard_nodes'),
    path('create_server', views.create_server, name='create_server')
]