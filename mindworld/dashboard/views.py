from django.shortcuts import render
from .kube_utils import get_kubernetes_nodes

# views.py in your Django app
from django.shortcuts import render, redirect
from kubernetes import client, config
from kubernetes.client import V1Namespace, V1ObjectMeta, V1Role, V1RoleBinding, V1RoleRef, V1PolicyRule
from kubernetes.client.rest import ApiException
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

@login_required
def create_server(request):
    if request.method == 'POST':
        username = request.user.username  # Get the username of the logged-in user
        namespace = f"{username}-namespace"  # Namespace named after the user

        config.load_kube_config()  # Load kube config from default location

        # Check if the namespace exists, and create it if not
        try:
            client.CoreV1Api().read_namespace(namespace)
        except ApiException as e:
            if e.status == 404:  # Namespace not found
                create_namespace_with_rbac(username, namespace)

        # Deployment logic as before, now specifying the namespace in deployment creation
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(
                name=request.POST.get('serverName'),
                annotations={
                    "minecraft-server-panel": "enabled",
                    "created-by": username  # Use the username as an annotation
                }
            ),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(
                    match_labels={"app": "minecraft-server"}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={"app": "minecraft-server"}
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="minecraft",
                                image="itzg/minecraft-server:latest",
                                ports=[client.V1ContainerPort(container_port=25565)],
                                env=[ # Add environment variables here as needed
                                    client.V1EnvVar(name="EULA", value="true"),
                                    # Additional environment variables can be added here
                                ]
                            )
                        ]
                    )
                )
            )
        )
        client.AppsV1Api().create_namespaced_deployment(namespace=namespace, body=deployment)
        return redirect('dashboard_home')  # Redirect to a success page

    return render(request, 'dashboard/create_server.html')

def create_namespace_with_rbac(username, namespace_name):
    config.load_kube_config()
    core_v1_api = client.CoreV1Api()
    rbac_api = client.RbacAuthorizationV1Api()

    # Create the namespace
    ns = client.V1Namespace(
        metadata=client.V1ObjectMeta(name=namespace_name)
    )
    core_v1_api.create_namespace(ns)

    # Create Role
    role = client.V1Role(
        metadata=client.V1ObjectMeta(namespace=namespace_name, name="namespace-manager"),
        rules=[
            client.V1PolicyRule(
                api_groups=["", "apps"],
                resources=["pods", "pods/exec", "pods/log", "deployments"],
                verbs=["get", "list", "watch", "create", "update", "patch", "delete"]
            )
        ]
    )
    rbac_api.create_namespaced_role(namespace=namespace_name, body=role)

    # Create RoleBinding
    role_binding = client.V1RoleBinding(
        metadata=client.V1ObjectMeta(namespace=namespace_name, name="namespace-manager-binding"),
        subjects=[{
            "kind": "User",
            "name": f"{username}@example.com",  # Adjust the domain as necessary
            "apiGroup": "rbac.authorization.k8s.io"
        }],
        role_ref=client.V1RoleRef(
            kind="Role",
            name="namespace-manager",
            api_group="rbac.authorization.k8s.io"
        )
    )
    rbac_api.create_namespaced_role_binding(namespace=namespace_name, body=role_binding)

@login_required
def dashboard_home(request):
    return render(request, 'dashboard/dashboard.html')

@login_required
def dashboard_nodes(request):
    nodes = get_kubernetes_nodes()
    return render(request, 'dashboard/nodes.html', {'nodes': nodes})