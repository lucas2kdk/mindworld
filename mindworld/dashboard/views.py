from django.shortcuts import render
from .kube_utils import get_kubernetes_nodes

# views.py in your Django app
from django.shortcuts import render, redirect
from kubernetes import client, config
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # Only if you're bypassing CSRF temporarily, recommended to handle CSRF properly
@login_required
def create_server(request):
    if request.method == 'POST':
        server_name = request.POST.get('serverName')
        server_type = request.POST.get('type')
        version = request.POST.get('version')
        motd = request.POST.get('motd')
        difficulty = request.POST.get('difficulty')
        max_players = request.POST.get('maxPlayers')
        eula = request.POST.get('eula') == 'on'

        if eula:  # Only create if EULA is agreed upon
            config.load_kube_config()  # Load kube config from default location, adjust for production
            apps_v1 = client.AppsV1Api()

            deployment = client.V1Deployment(
                api_version="apps/v1",
                kind="Deployment",
                metadata=client.V1ObjectMeta(
                    name=server_name,
                    annotations={
                        "minecraft-server-panel": "enabled",
                        "created-by": request.user.username  # Assuming the user is logged in
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
                                    resources=client.V1ResourceRequirements(
                                        limits={"cpu": "1", "memory": "1Gi"},
                                        requests={"cpu": "500m", "memory": "500Mi"}
                                    ),
                                    env=[
                                        client.V1EnvVar(name="EULA", value="true"),
                                        client.V1EnvVar(name="TYPE", value=server_type),
                                        client.V1EnvVar(name="VERSION", value=version),
                                        client.V1EnvVar(name="MOTD", value=motd),
                                        client.V1EnvVar(name="DIFFICULTY", value=difficulty),
                                        client.V1EnvVar(name="MAX_PLAYERS", value=max_players),
                                    ]
                                )
                            ]
                        )
                    )
                )
            )
            apps_v1.create_namespaced_deployment(namespace="default", body=deployment)
            return redirect('dashboard_home')  # Redirect to a success page or back to form with a success message
        else:
            return render(request, 'dashboard/create_server.html', {'error': 'You must agree to the Minecraft EULA.'})
    else:
        return render(request, 'dashboard/create_server.html')



def dashboard_home(request):
    return render(request, 'dashboard/dashboard.html')

def dashboard_nodes(request):
    nodes = get_kubernetes_nodes()
    return render(request, 'dashboard/nodes.html', {'nodes': nodes})