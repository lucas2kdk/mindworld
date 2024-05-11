from django.shortcuts import render, redirect
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from .kube_utils import get_kubernetes_nodes


def create_server(request):
    if request.method == 'POST':
        username = request.user.username
        namespace = f"{username}-namespace"
        server_name = request.POST.get('serverName', 'default-minecraft-server')

        config.load_kube_config()
        apps_v1_api = client.AppsV1Api()
        core_v1_api = client.CoreV1Api()

        # Check if the namespace exists
        try:
            core_v1_api.read_namespace(name=namespace)
        except ApiException as e:
            if e.status == 404:  # Namespace not found
                create_namespace_with_rbac(username, namespace)

        # Define the deployment
        deployment_body = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(
                name=server_name,
                namespace=namespace,
                annotations={
                    "minecraft-server-panel": "enabled",
                    "created-by": username
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
                                env=[client.V1EnvVar(name="EULA", value="true")],
                                resources=client.V1ResourceRequirements(
                                    requests={"cpu": "500m", "memory": "500Mi"},
                                    limits={"cpu": "1", "memory": "1Gi"}
                                )
                            )
                        ]
                    )
                )
            )
        )

        # Create or update the deployment
        try:
            apps_v1_api.create_namespaced_deployment(namespace=namespace, body=deployment_body)
            print("Deployment created successfully.")
        except ApiException as e:
            print("Error creating deployment:", e)
            return render(request, 'dashboard/create_server.html', {'error': str(e)})

        return redirect('dashboard_home')

    return render(request, 'dashboard/create_server.html')


def stop_server(request, namespace, deployment_name):
    config.load_kube_config()
    apps_v1_api = client.AppsV1Api()

    # Patch the deployment to set replicas to 0
    body = {'spec': {'replicas': 0}}
    try:
        apps_v1_api.patch_namespaced_deployment_scale(deployment_name, namespace, body)
        print(f"Deployment {deployment_name} in {namespace} stopped successfully.")
    except ApiException as e:
        print(f"Failed to stop deployment: {e}")
        # Optionally, redirect to an error handling page or display an error message

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def start_server(request, namespace, deployment_name):
    config.load_kube_config()
    apps_v1_api = client.AppsV1Api()

    # Patch the deployment to set replicas to 1
    body = {'spec': {'replicas': 1}}
    try:
        apps_v1_api.patch_namespaced_deployment_scale(deployment_name, namespace, body)
        print(f"Deployment {deployment_name} in {namespace} started successfully.")
    except ApiException as e:
        print(f"Failed to start deployment: {e}")
        # Optionally, redirect to an error handling page or display an error message

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def create_namespace_with_rbac(username, namespace_name):
    config.load_kube_config()
    core_v1_api = client.CoreV1Api()
    rbac_api = client.RbacAuthorizationV1Api()

    # Create the namespace
    ns = client.V1Namespace(
        metadata=client.V1ObjectMeta(name=namespace_name)
    )
    try:
        core_v1_api.create_namespace(ns)
        print(f"Namespace {namespace_name} created successfully.")
    except ApiException as e:
        if e.status != 409:  # Ignore error if namespace already exists
            raise

    # Define and create a Role
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

    # Define and create a RoleBinding
    role_binding = client.V1RoleBinding(
        metadata=client.V1ObjectMeta(namespace=namespace_name, name="namespace-manager-binding"),
        subjects=[{
            "kind": "User",
            "name": f"{username}@example.com",  # Customize the user's domain as necessary
            "apiGroup": "rbac.authorization.k8s.io"
        }],
        role_ref=client.V1RoleRef(
            kind="Role",
            name="namespace-manager",
            api_group="rbac.authorization.k8s.io"
        )
    )
    rbac_api.create_namespaced_role_binding(namespace=namespace_name, body=role_binding)
    print(f"RoleBinding 'namespace-manager-binding' created for {username}.")


@login_required
def dashboard_home(request):
    return render(request, 'dashboard/dashboard.html')


@login_required
def dashboard_nodes(request):
    nodes = get_kubernetes_nodes()
    return render(request, 'dashboard/nodes.html', {'nodes': nodes})