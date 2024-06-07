# routing.py
from django.urls import path, re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/nodes/$', consumers.NodesConsumer.as_asgi()),
    path('ws/servers/', consumers.ServerStatusConsumer.as_asgi()),
    path('ws/k8s-console/<str:namespace>/<str:deployment_name>/', consumers.ConsoleConsumer.as_asgi()),
]
