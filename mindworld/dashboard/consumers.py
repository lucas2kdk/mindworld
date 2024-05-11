import asyncio
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .kube_utils import get_kubernetes_nodes, get_user_deployments, get_all_deployment_statuses
import logging

logger = logging.getLogger(__name__)

class NodeInfoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.task = asyncio.create_task(self.send_node_data())

    async def disconnect(self, close_code):
        if self.task:
            self.task.cancel()
            await self.task  # Ensure the task cancellation is awaited

    async def send_node_data(self):
        try:
            while True:
                node_data = await database_sync_to_async(get_kubernetes_nodes)()
                logger.info(f"Sending node data: {node_data}")  # Use logger instead of print
                await self.send(json.dumps({'nodes': node_data}))
                await asyncio.sleep(10)  # Update interval
        except asyncio.CancelledError:
            logger.info("Node data sending task was cancelled")

    async def receive(self, text_data=None, bytes_data=None):
        # Handle incoming messages (if necessary for your application)
        pass


class ServerStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            await self.accept()
            self.task = asyncio.create_task(self.send_server_status())
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.task:
            self.task.cancel()
            await self.task  # Ensure the task cancellation is awaited

    async def send_server_status(self):
        try:
            while True:
                deployments = await self.get_deployments(self.scope["user"].username)
                logger.info(f"Deployments fetched: {deployments}")  # Log fetched data
                await self.send(json.dumps({'type': 'server.status', 'data': deployments}))
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            logger.info("Server status update task was cancelled")

    @database_sync_to_async
    def get_deployments(self, username):
        return get_user_deployments(username)

    # If you need to broadcast updates to a group, you should set up a group in `connect` and use it here
    async def broadcast_deployment_status(self):
        deployments = await self.get_deployments(self.scope["user"].username)
        message = {
            'type': 'server.status.update',
            'data': deployments
        }
        await self.channel_layer.group_send('deployment_status_group', {
            'type': 'websocket.send',
            'text': json.dumps(message)
        })
