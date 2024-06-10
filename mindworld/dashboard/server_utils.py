import os
import logging
from kubernetes import client, config
from kubernetes.stream import stream
from kubernetes.client.rest import ApiException
from websocket import WebSocketConnectionClosedException

# Configuration Management
NAMESPACE = os.getenv('NAMESPACE', 'default')
CONTAINER_NAME = os.getenv('CONTAINER_NAME', 'minecraft-server')

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# def load_kube_config():
#     """Load Kubernetes configuration."""
#     try:
#         config.load_kube_config()
#         #logger.info("Kubernetes configuration loaded successfully.")
#     except Exception as e:
#         #logger.error(f"Failed to load Kubernetes configuration: {e}")
#         raise

def load_kube_config():
    """Load Kubernetes configuration."""
    try:
        config.load_incluster_config()
        logger.info("Kubernetes configuration loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load Kubernetes configuration: {e}")
        raise

def get_statefulsets_managed_by_mindworld():
    load_kube_config()
    api_instance = client.AppsV1Api()
    
    try:
        statefulsets = api_instance.list_namespaced_stateful_set(namespace=NAMESPACE)
        
        managed_statefulsets = []
        
        for sts in statefulsets.items:
            annotations = sts.metadata.annotations
            if annotations and annotations.get("managed-by") == "mindworld":
                managed_statefulsets.append({
                    "name": sts.metadata.name,
                    "status": "Running" if sts.status.ready_replicas == sts.spec.replicas else "Stopped",
                    "running_replicas": sts.status.ready_replicas,
                    "replicas": sts.spec.replicas,
                    "namespace": sts.metadata.namespace
                })
        
        return managed_statefulsets

    except ApiException as e:
        logger.error(f"Exception when calling AppsV1Api->list_namespaced_stateful_set: {e}")
        return []

def scale_statefulset(namespace, name, replicas):
    load_kube_config()
    api_instance = client.AppsV1Api()
    
    try:
        body = {'spec': {'replicas': replicas}}
        api_instance.patch_namespaced_stateful_set_scale(name, namespace, body)
        logger.info(f"Scaled {name} to {replicas} replicas.")
    except ApiException as e:
        logger.error(f"Exception when calling AppsV1Api->patch_namespaced_stateful_set_scale: {e}")

def create_or_update_statefulset_and_service(name, env_vars):
    load_kube_config()
    api_instance = client.AppsV1Api()
    core_api_instance = client.CoreV1Api()

    # Convert all environment variable values to strings
    env_vars = {key: str(value) for key, value in env_vars.items()}

    # Generate service names
    statefulset_name = name
    service_name = f"{name}-service"

    statefulset_manifest = {
        "apiVersion": "apps/v1",
        "kind": "StatefulSet",
        "metadata": {
            "name": statefulset_name,
            "annotations": {
                "managed-by": "mindworld"
            }
        },
        "spec": {
            "serviceName": service_name,
            "replicas": 1,
            "selector": {
                "matchLabels": {
                    "app": "minecraft-server"
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "minecraft-server"
                    }
                },
                "spec": {
                    "containers": [{
                        "name": "minecraft-server",
                        "image": "itzg/minecraft-server",
                        "env": [{"name": key, "value": value} for key, value in env_vars.items()],
                        "ports": [{"containerPort": 25565}],
                        "command": ["/bin/sh", "-c", "apt-get update && apt-get install -y screen && screen -dmS minecraft /start && tail -f /dev/null"],
                        "stdin": True,
                        "tty": True,
                        "volumeMounts": [{"mountPath": "/data", "name": "minecraft-data"}],
                        "resources": {
                            "requests": {"cpu": "500m", "memory": "2Gi"},
                            "limits": {"cpu": 1, "memory": "2Gi"}
                        },
                        "livenessProbe": {
                            "exec": {"command": ["mc-health"]},
                            "initialDelaySeconds": 120,
                            "periodSeconds": 60
                        },
                        "readinessProbe": {
                            "exec": {"command": ["mc-health"]},
                            "initialDelaySeconds": 20,
                            "periodSeconds": 10,
                            "failureThreshold": 12
                        }
                    }]
                }
            },
            "volumeClaimTemplates": [{
                "metadata": {"name": "minecraft-data"},
                "spec": {
                    "accessModes": ["ReadWriteOnce"],
                    "resources": {"requests": {"storage": "1Gi"}}
                }
            }]
        }
    }

    service_manifest = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": service_name,
            "annotations": {
                "managed-by": "mindworld"
            }
        },
        "spec": {
            "selector": {
                "app": "minecraft-server"
            },
            "ports": [{
                "protocol": "TCP",
                "port": 25565,
                "targetPort": 25565
            }],
            "type": "ClusterIP"
        }
    }

    try:
        api_instance.replace_namespaced_stateful_set(name=statefulset_name, namespace=NAMESPACE, body=statefulset_manifest)
        logger.info("StatefulSet updated successfully!")
    except ApiException as e:
        if e.status == 404:
            try:
                api_instance.create_namespaced_stateful_set(namespace=NAMESPACE, body=statefulset_manifest)
                logger.info("StatefulSet created successfully!")
            except ApiException as e:
                logger.error(f"Error creating StatefulSet: {e}")
        else:
            logger.error(f"Error updating StatefulSet: {e}")

    try:
        core_api_instance.replace_namespaced_service(name=service_name, namespace=NAMESPACE, body=service_manifest)
        logger.info("ClusterIP service updated successfully!")
    except ApiException as e:
        if e.status == 404:
            try:
                core_api_instance.create_namespaced_service(namespace=NAMESPACE, body=service_manifest)
                logger.info("ClusterIP service created successfully!")
            except ApiException as e:
                logger.error(f"Error creating ClusterIP service: {e}")
        else:
            logger.error(f"Error updating ClusterIP service: {e}")

def get_pod_name(statefulset_name):
    """Get the name of the pod running the Minecraft server."""
    return f"{statefulset_name}-0"

def attach_to_console(pod_name):
    """Attach to the Minecraft server console using WebSocket."""
    try:
        logger.info("Connecting to the Minecraft server console...")
        # Check for existing screen sessions
        screen_list_command = ['screen', '-ls']
        response = stream(client.CoreV1Api().connect_get_namespaced_pod_exec,
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
        ws_client = stream(client.CoreV1Api().connect_get_namespaced_pod_exec,
                           pod_name,
                           NAMESPACE,
                           command=exec_command,
                           container=CONTAINER_NAME,
                           stderr=True, stdin=True,
                           stdout=True, tty=True,
                           _preload_content=False)

        logger.info("WebSocket connection established.")

        return ws_client

    except Exception as e:
        logger.error(f"Error attaching to console: {e}")
        raise

def list_kubernetes_nodes():
    """List all Kubernetes nodes."""
    load_kube_config()
    api_instance = client.CoreV1Api()
    
    try:
        nodes = api_instance.list_node()
        node_list = []
        
        for node in nodes.items:
            node_info = {
                "name": node.metadata.name,
                "status": node.status.conditions[-1].type,
                "address": node.status.addresses[0].address,
                "os_image": node.status.node_info.os_image,
                "kubelet_version": node.status.node_info.kubelet_version
            }
            node_list.append(node_info)
        
        return node_list

    except ApiException as e:
        logger.error(f"Exception when calling CoreV1Api->list_node: {e}")
        return []