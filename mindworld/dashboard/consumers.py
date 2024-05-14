import asyncio
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .kube_utils import get_kubernetes_nodes, get_user_resources  # Make sure get_user_resources can handle both types
import logging
from kubernetes import client, config
from kubernetes.stream import stream

logger = logging.getLogger(__name__)

class NodeInfoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.task = asyncio.create_task(self.send_node_data())

    async def disconnect(self, close_code):
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                logger.info("Task was cancelled due to WebSocket disconnection")

    async def send_node_data(self):
        while True:
            node_data = await database_sync_to_async(get_kubernetes_nodes)()
            logger.info(f"Sending node data: {node_data}")
            await self.send(json.dumps({'nodes': node_data}))
            await asyncio.sleep(10)

class ServerStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            self.resource_type = self.scope['url_route']['kwargs'].get('resource_type', 'deployment')  # Expecting 'deployment' or 'statefulset'
            await self.accept()
            self.task = asyncio.create_task(self.send_resource_status())
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                logger.info("Task was cancelled due to WebSocket disconnection")

    async def send_resource_status(self):
        while True:
            resource_status = await self.get_resources(self.scope["user"].username, self.resource_type)
            logger.info(f"{self.resource_type.capitalize()}s fetched: {resource_status}")
            await self.send(json.dumps({'type': 'resource.status', 'data': resource_status}))
            await asyncio.sleep(10)

    @database_sync_to_async
    def get_resources(self, username, resource_type):
        return get_user_resources(username, resource_type)  # This function must handle 'deployment' and 'statefulset'

class KubernetesConsoleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.namespace = self.scope['url_route']['kwargs']['namespace']
        self.deployment_name = self.scope['url_route']['kwargs']['deploymentName']
        config.load_kube_config()
        self.core_v1_api = client.CoreV1Api()
        await self.accept()

    async def disconnect(self, close_code):
        logger.info(f"Disconnected with close code: {close_code}")

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            try:
                text_data_json = json.loads(text_data)
                command = text_data_json.get('command')
                if command:
                    pod_name = await self.get_first_pod_name(self.deployment_name, self.namespace)
                    if pod_name:
                        response = await self.exec_command(pod_name, self.namespace, command)
                        await self.send(text_data=json.dumps({'message': response}))
                    else:
                        await self.send(text_data=json.dumps({'error': 'No pod found for the given deployment'}))
                else:
                    await self.send(text_data=json.dumps({'error': 'No command received'}))
            except json.JSONDecodeError:
                await self.send(text_data=json.dumps({'error': 'Invalid JSON format'}))

    async def get_first_pod_name(self, deployment_name, namespace):
        try:
            pods = self.core_v1_api.list_namespaced_pod(namespace, label_selector=f"app={deployment_name}")
            if pods.items:
                return pods.items[0].metadata.name
        except client.exceptions.ApiException as e:
            logger.error(f"API Exception when fetching pods: {e}")
            return None

    async def exec_command(self, pod_name, namespace, command):
        exec_command = ['/bin/sh', '-c', command]
        try:
            resp = stream(self.core_v1_api.connect_get_namespaced_pod_exec,
                          pod_name, namespace,
                          command=exec_command,
                          stderr=True, stdin=True,
                          stdout=True, tty=False,
                          _preload_content=False)
            stdout, stderr = resp.read_stdout(), resp.read_stderr()
            return f"STDOUT: {stdout}\nSTDERR: {stderr}"
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            return f"Failed to execute command: {str(e)}"
