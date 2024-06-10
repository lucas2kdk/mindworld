# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create-server/', views.create_server, name='create_server'),
    path('stop-server/<str:namespace>/<str:name>/', views.stop_server, name='stop_server'),
    path('start-server/<str:namespace>/<str:name>/', views.start_server, name='start_server'),
    path('restart-server/<str:namespace>/<str:name>/', views.restart_server, name='restart_server'),
    path('edit-server/<str:namespace>/<str:name>/', views.edit_server, name='edit_server'),
    path('manage-server/<str:namespace>/<str:name>/<str:action>/', views.manage_server, name='manage_server'),
    path('api/server-status/', views.get_server_status, name='get_server_status'),
    path('nodes/', views.nodes, name='nodes'),

]
