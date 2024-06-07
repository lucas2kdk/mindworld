# minecraft/routing.py

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/console/', consumers.ConsoleConsumer.as_asgi()),
]
