import asyncio
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .kube_utils import get_kubernetes_nodes, get_user_deployments, get_all_deployment_statuses
import logging

logging.basicConfig(level=logging.INFO)
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
                print(f"Sending node data: {node_data}")  # Debugging statement
                await self.send(json.dumps({'nodes': node_data}))
                await asyncio.sleep(10)  # Update interval
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            pass

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

    # Example snippet in your Django Channels consumer
    async def send_deployment_status_update(self):
        message = {
            'type': 'server.status.update',
            'data': get_all_deployment_statuses()
        }
        await self.channel_layer.group_send('deployment_status_group', {
            'type': 'websocket.send',
            'text': json.dumps(message)
        })


    async def send_server_status(self):
        try:
            while True:
                deployments = await self.get_deployments(self.scope["user"].username)
                logging.info(f"Deployments fetched: {deployments}")  # Log fetched data
                await self.send(json.dumps({'type': 'server.status', 'data': deployments}))
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            pass

    @database_sync_to_async
    def get_deployments(self, username):
        deployments = get_user_deployments(username)
        logging.info(f"Fetching deployments for {username}: {deployments}")  # Log fetching process
        return deployments