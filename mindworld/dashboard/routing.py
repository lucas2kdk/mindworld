# k8smonitor/routing.py
from django.urls import re_path
from .consumers import NodeInfoConsumer, ServerStatusConsumer

websocket_urlpatterns = [
    re_path(r'ws/nodes/', NodeInfoConsumer.as_asgi()),
    re_path(r'^ws/servers/$', ServerStatusConsumer.as_asgi()),
]