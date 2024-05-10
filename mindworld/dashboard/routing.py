# k8smonitor/routing.py
from django.urls import re_path
from .consumers import NodeInfoConsumer

websocket_urlpatterns = [
    re_path(r'ws/nodes/', NodeInfoConsumer.as_asgi()),
]