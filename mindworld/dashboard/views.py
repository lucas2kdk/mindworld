from django.shortcuts import render, redirect
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from .kube_utils import get_kubernetes_nodes

@login_required
def create_server(request):
    if request.method == 'POST':
        username = request.user.username
        namespace = f"{username}-namespace"
        server_name = request.POST.get('serverName', 'default-minecraft-server')

        config.load_kube_config()
        apps_v1_api = client.AppsV1Api()
        core_v1_api = client.CoreV1Api()

        # Check if the namespace exists, if not, create it
        try:
            core_v1_api.read_namespace(name=namespace)
        except ApiException as e:
            if e.status == 404:  # Namespace not found
                create_namespace_with_rbac(username, namespace)

        # Prepare the StatefulSet specification including the 'created-by' annotation
        statefulset_body = create_statefulset_spec(namespace, server_name, username)

        # Attempt to create the StatefulSet
        try:
            apps_v1_api.create_namespaced_stateful_set(namespace=namespace, body=statefulset_body)
            print("StatefulSet created successfully.")
        except ApiException as e:
            print("Error creating StatefulSet:", e)
            return render(request, 'dashboard/create_server.html', {'error': str(e)})

        return redirect('dashboard_home')

    return render(request, 'dashboard/create_server.html')

def create_statefulset_spec(namespace, server_name, username):
    # Define the container for the StatefulSet
    container = client.V1Container(
        name="minecraft",
        image="itzg/minecraft-server:latest",
        ports=[client.V1ContainerPort(container_port=25565)],
        env=[client.V1EnvVar(name="EULA", value="true")]
    )

    # Define the Pod template with annotations
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(
            labels={"app": "minecraft-server"},
            annotations={"created-by": username}  # Adding user annotation to the pod template
        ),
        spec=client.V1PodSpec(containers=[container])
    )

    # Define volume claim template for persistent storage
    volume_claim_template = client.V1PersistentVolumeClaim(
        metadata=client.V1ObjectMeta(name="minecraft-data"),
        spec=client.V1PersistentVolumeClaimSpec(
            access_modes=["ReadWriteMany"],
            storage_class_name="longhorn-rwx",
            resources=client.V1ResourceRequirements(requests={"storage": "1Gi"})
        )
    )

    # StatefulSet metadata including annotations
    statefulset_metadata = client.V1ObjectMeta(
        name=server_name,
        namespace=namespace,
        annotations={"created-by": username}  # Adding user annotation to the StatefulSet metadata
    )

    # Create the StatefulSet spec
    statefulset_spec = client.V1StatefulSetSpec(
        service_name=server_name,
        replicas=1,
        selector=client.V1LabelSelector(match_labels={"app": "minecraft-server"}),
        template=template,
        volume_claim_templates=[volume_claim_template]
    )

    # Return the StatefulSet with all configurations
    return client.V1StatefulSet(
        api_version="apps/v1",
        kind="StatefulSet",
        metadata=statefulset_metadata,
        spec=statefulset_spec
    )


def create_namespace_with_rbac(username, namespace_name):
    config.load_kube_config()
    core_v1_api = client.CoreV1Api()
    rbac_api = client.RbacAuthorizationV1Api()

    # Create the namespace
    ns = client.V1Namespace(
        metadata=client.V1ObjectMeta(name=namespace_name)
    )
    core_v1_api.create_namespace(ns)

    # Define and create a Role
    role = client.V1Role(
        metadata=client.V1ObjectMeta(namespace=namespace_name, name="namespace-manager"),
        rules=[
            client.V1PolicyRule(
                api_groups=["", "apps"],
                resources=["pods", "pods/exec", "pods/log", "deployments", "statefulsets"],
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
            "name": f"{username}",
            "apiGroup": "rbac.authorization.k8s.io"
        }],
        role_ref=client.V1RoleRef(
            kind="Role",
            name="namespace-manager",
            api_group="rbac.authorization.k8s.io"
        )
    )
    rbac_api.create_namespaced_role_binding(namespace=namespace_name, body=role_binding)



def stop_server(request, namespace, statefulset_name):
    config.load_kube_config()
    apps_v1_api = client.AppsV1Api()

    # Prepare the patch to set replicas to 0
    body = {'spec': {'replicas': 0}}
    try:
        # Patch the StatefulSet to scale it down to 0
        apps_v1_api.patch_namespaced_stateful_set_scale(name=statefulset_name, namespace=namespace, body=body)
        print(f"StatefulSet {statefulset_name} in {namespace} stopped successfully.")
    except ApiException as e:
        print(f"Failed to stop StatefulSet: {e}")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
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


@login_required
def edit_server(request, namespace, deployment_name):
    context = {
        'namespace': namespace,
        'deployment_name': deployment_name
    }
    return render(request, 'dashboard/edit_server.html', context)

@login_required
def dashboard_home(request):
    return render(request, 'dashboard/dashboard.html')


@login_required
def dashboard_nodes(request):
    nodes = get_kubernetes_nodes()
    return render(request, 'dashboard/nodes.html', {'nodes': nodes})