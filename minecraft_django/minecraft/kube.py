# minecraft/kube.py

import logging
import os
from kubernetes import client, config
from kubernetes.stream import stream
import threading
from websocket import WebSocketConnectionClosedException

logger = logging.getLogger(__name__)

NAMESPACE = os.getenv('NAMESPACE', 'default')
STATEFULSET_NAME = os.getenv('STATEFULSET_NAME', 'minecraft-server')
CONTAINER_NAME = os.getenv('CONTAINER_NAME', 'minecraft-server')

def load_kube_config():
    """Load Kubernetes configuration."""
    try:
        config.load_kube_config()
        logger.info("Kubernetes configuration loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load Kubernetes configuration: {e}")
        raise

def get_kubernetes_client():
    """Get the Kubernetes API client."""
    return client.CoreV1Api()

def get_pod_name(v1):
    """Get the name of the pod running the Minecraft server."""
    try:
        pod_list = v1.list_namespaced_pod(namespace=NAMESPACE, label_selector=f"app={STATEFULSET_NAME}")
        for pod in pod_list.items:
            return pod.metadata.name
        raise Exception("No pod found for the Minecraft server.")
    except Exception as e:
        logger.error(f"Error getting pod name: {e}")
        raise

def execute_command(v1, command):
    """Execute a command in the Minecraft server pod."""
    try:
        pod_name = get_pod_name(v1)
        exec_command = ['/bin/sh', '-c', command]
        response = stream(v1.connect_get_namespaced_pod_exec,
                          pod_name,
                          NAMESPACE,
                          command=exec_command,
                          container=CONTAINER_NAME,
                          stderr=True, stdin=False,
                          stdout=True, tty=False)
        logger.info(f"Command executed: {command}")
        logger.info(response)
        return response
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        raise

def attach_to_console(v1, ws_client, console_output_callback):
    """Attach to the Minecraft server console using WebSocket."""
    try:
        pod_name = get_pod_name(v1)

        # Check for existing screen sessions
        screen_list_command = ['screen', '-ls']
        response = stream(v1.connect_get_namespaced_pod_exec,
                          pod_name,
                          NAMESPACE,
                          command=screen_list_command,
                          container=CONTAINER_NAME,
                          stderr=True, stdin=False,
                          stdout=True, tty=False)
        screens = response.splitlines()
        minecraft_screen = None

        for screen in screens:
            if 'minecraft' in screen:
                minecraft_screen = screen.split('.')[0].strip()
                break

        if not minecraft_screen:
            raise Exception("No Minecraft screen session found.")

        exec_command = ['screen', '-x', minecraft_screen]
        ws_client = stream(v1.connect_get_namespaced_pod_exec,
                           pod_name,
                           NAMESPACE,
                           command=exec_command,
                           container=CONTAINER_NAME,
                           stderr=True, stdin=True,
                           stdout=True, tty=True,
                           _preload_content=False)

        def read_console_output(ws_client):
            """Read and print console output."""
            try:
                while True:
                    message = ws_client.read_stdout()
                    if message:
                        console_output_callback(message)
            except WebSocketConnectionClosedException:
                logger.warning("WebSocket connection closed.")

        thread = threading.Thread(target=read_console_output, args=(ws_client,))
        thread.start()

        return ws_client
    except Exception as e:
        logger.error(f"Error attaching to console: {e}")
        raise
