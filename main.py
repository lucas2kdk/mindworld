import os
import logging
import threading
from kubernetes import client, config
from kubernetes.stream import stream
from websocket import WebSocketConnectionClosedException

# Configuration Management
NAMESPACE = os.getenv('NAMESPACE', 'default')
STATEFULSET_NAME = os.getenv('STATEFULSET_NAME', 'minecraft-server')
CONTAINER_NAME = os.getenv('CONTAINER_NAME', 'minecraft-server')

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        raise

def attach_to_console(v1):
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
                        logger.info(message)
            except WebSocketConnectionClosedException:
                logger.warning("WebSocket connection closed.")

        thread = threading.Thread(target=read_console_output, args=(ws_client,))
        thread.start()

        # Keep the main thread running to send commands
        try:
            while True:
                command = input("Enter Minecraft console command: ")
                ws_client.write_stdin(command + "\n")
        except KeyboardInterrupt:
            logger.info("Closing WebSocket connection.")
            ws_client.write_stdin("exit\n")
            ws_client.close()
        except Exception as e:
            logger.error(f"An error occurred while sending command: {e}")
    except Exception as e:
        logger.error(f"Error attaching to console: {e}")
        raise

def main():
    """Main function to execute commands and attach to the console."""
    try:
        load_kube_config()
        v1 = get_kubernetes_client()

        # Send a command to the Minecraft server
        execute_command(v1, "screen -S minecraft -X stuff 'say Hello from Kubernetes StatefulSet!\\n'")
        
        # Attach to the Minecraft server console
        attach_to_console(v1)
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
