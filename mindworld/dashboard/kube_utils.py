# k8smonitor/kube_utils.py
from kubernetes import client, config

def get_kubernetes_nodes():
    config.load_kube_config()  # Load the kubeconfig file
    v1 = client.CoreV1Api()
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