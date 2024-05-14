from kubernetes import client, config
import logging

logger = logging.getLogger(__name__)

def get_kubernetes_nodes():
    config.load_kube_config()
    v1 = client.CoreV1Api()
    try:
        nodes = v1.list_node()
        node_details = []
        for node in nodes.items:
            conditions = {condition.type: condition.status for condition in node.status.conditions}
            node_details.append({
                'name': node.metadata.name,
                'status': 'Ready' if conditions.get('Ready', '') == 'True' else 'Not Ready',
                'pods': sum(1 for _ in v1.list_pod_for_all_namespaces(field_selector=f"spec.nodeName={node.metadata.name}").items),
                'ip': node.status.addresses[0].address,
                'os': node.status.node_info.os_image,
            })
        return node_details
    except Exception as e:
        logger.error(f"Failed to fetch nodes: {e}")
        return []

def get_user_resources(username, resource_type):
    config.load_kube_config()
    apps_v1 = client.AppsV1Api()
    resources = []
    if resource_type == 'statefulset':
        all_resources = apps_v1.list_stateful_set_for_all_namespaces()
    elif resource_type == 'deployment':
        all_resources = apps_v1.list_deployment_for_all_namespaces()
    else:
        logger.error(f"Unsupported resource type: {resource_type}")
        return []

    for res in all_resources.items:
        annotations = res.metadata.annotations or {}
        logger.debug(f"Resource {res.metadata.name} annotations: {annotations}")
        if annotations.get('created-by') == username:
            logger.debug(f"Resource {res.metadata.name} added")
            resource_status = 'Running' if res.status.ready_replicas == res.spec.replicas else 'Not fully running'
            resources.append({
                'name': res.metadata.name,
                'namespace': res.metadata.namespace,
                'status': resource_status,
                'replicas': res.spec.replicas,
                'ready_replicas': res.status.ready_replicas
            })

    logger.info(f"Returning resources: {resources}")
    return resources


def get_all_resource_statuses(resource_type='deployment'):
    config.load_kube_config()
    v1 = client.AppsV1Api()
    resource_statuses = []
    try:
        if resource_type == 'deployment':
            resources = v1.list_deployment_for_all_namespaces()
        elif resource_type == 'statefulset':
            resources = v1.list_stateful_set_for_all_namespaces()
        for resource in resources.items:
            status = 'Running' if resource.status.ready_replicas > 0 else 'Stopped'
            resource_statuses.append({
                'name': resource.metadata.name,
                'namespace': resource.metadata.namespace,
                'status': status,
                'replicas': resource.spec.replicas,
                'ready_replicas': resource.status.ready_replicas
            })
        logger.debug(f"{resource_type.title()} statuses fetched: {resource_statuses}")
        return resource_statuses
    except Exception as e:
        logger.error(f"Failed to fetch {resource_type} statuses: {e}")
        return []

def get_user_resources(username, resource_type='deployment'):
    config.load_kube_config()
    apps_v1 = client.AppsV1Api()
    resources = []
    try:
        resource_list = {
            'deployment': apps_v1.list_deployment_for_all_namespaces,
            'statefulset': apps_v1.list_stateful_set_for_all_namespaces
        }

        if resource_type not in resource_list:
            logger.error(f"Unsupported resource type: {resource_type}")
            return []

        all_resources = resource_list[resource_type]()

        for resource in all_resources.items:
            annotations = resource.metadata.annotations or {}
            if annotations.get('created-by') == username:
                ready_replicas = resource.status.ready_replicas if resource.status.ready_replicas is not None else 0
                status = 'Running' if ready_replicas == resource.spec.replicas else 'Not fully running'
                resources.append({
                    'name': resource.metadata.name,
                    'namespace': resource.metadata.namespace,
                    'status': status,
                    'replicas': resource.spec.replicas,
                    'ready_replicas': ready_replicas
                })

        logger.debug(f"Filtered resources: {resources}")

        logger.debug(f"Fetched resources: {resources}")
        if not resources:
            logger.warning("No resources found, check filters and Kubernetes API responses")

        return resources

    except Exception as e:
        logger.error(f"Failed to fetch resources for {resource_type}: {e}")
        return []

