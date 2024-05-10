# k8smonitor/consumers.py
import asyncio
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .kube_utils import get_kubernetes_nodes

class NodeInfoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.accepted = False
        await self.accept()
        self.accepted = True
        self.task = asyncio.get_event_loop().create_task(self.send_node_data())

    async def disconnect(self, close_code):
        # Cancel the background task
        self.accepted = False
        if self.task:
            self.task.cancel()
        await self.task

    async def send_node_data(self):
        try:
            while self.accepted:
                node_data = get_kubernetes_nodes()
                await self.send(json.dumps({'nodes': node_data}))
                await asyncio.sleep(10)  # Update interval
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            pass

    async def receive(self, text_data=None, bytes_data=None):
        # Handle incoming messages (if necessary for your application)
        pass
