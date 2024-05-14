# k8smonitor/routing.py
from django.urls import re_path
from .consumers import NodeInfoConsumer, ServerStatusConsumer, KubernetesConsoleConsumer

websocket_urlpatterns = [
    re_path(r'ws/nodes/', NodeInfoConsumer.as_asgi()),
    re_path(r'^ws/servers/$', ServerStatusConsumer.as_asgi()),
    re_path(r'^ws/k8s-console/(?P<namespace>[^/]+)/(?P<deploymentName>[^/]+)/$', KubernetesConsoleConsumer.as_asgi()),
]