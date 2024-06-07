import json
import threading
from channels.generic.websocket import AsyncWebsocketConsumer
from .server_utils import attach_to_console, get_pod_name, load_kube_config, get_statefulsets_managed_by_mindworld, list_kubernetes_nodes
from websocket import WebSocketConnectionClosedException
from asgiref.sync import async_to_sync
import logging
import asyncio

logger = logging.getLogger(__name__)

class NodesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.thread = threading.Thread(target=self.send_node_status)
        self.thread.start()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("nodes", self.channel_name)

    async def receive(self, text_data):
        pass

    def send_node_status(self):
        while True:
            nodes = list_kubernetes_nodes()
            async_to_sync(self.send)(text_data=json.dumps({
                'type': 'node.status',
                'data': nodes
            }))

class ConsoleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.namespace = self.scope['url_route']['kwargs']['namespace']
        self.deployment_name = self.scope['url_route']['kwargs']['deployment_name']
        
        self.pod_name = get_pod_name(self.deployment_name)

        load_kube_config()
        self.ws_client = attach_to_console(self.pod_name)

        await self.accept()

        self.thread = threading.Thread(target=self.read_console_output)
        self.thread.start()

    async def disconnect(self, close_code):
        self.ws_client.write_stdin("exit\n")
        self.ws_client.close()

    async def receive(self, text_data):
        command = json.loads(text_data).get('command')
        if command:
            self.ws_client.write_stdin(command + "\n")

    def read_console_output(self):
        try:
            while True:
                message = self.ws_client.read_stdout()
                if message:
                    formatted_message = message.replace("\r", "").replace("\n", "\n")
                    logger.info(f"Console output: {formatted_message}")
                    async_to_sync(self.send)(text_data=json.dumps({'message': formatted_message}))
        except WebSocketConnectionClosedException:
            logger.warning("WebSocket connection closed.")

class ServerStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("servers", self.channel_name)
        await self.accept()

        # Send initial server status data
        servers = get_statefulsets_managed_by_mindworld()
        await self.send(text_data=json.dumps({
            'type': 'server.status',
            'data': servers
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("servers", self.channel_name)

    async def receive(self, text_data):
        pass

    async def server_status(self, event):
        servers = event['servers']
        await self.send(text_data=json.dumps({
            'type': 'server.status',
            'data': servers
        }))
