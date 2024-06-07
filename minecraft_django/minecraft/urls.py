# minecraft/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('command/', views.command_view, name='command'),
    path('console/', views.console_view, name='console'),
]
