import os
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .forms import CreateServerForm
from .server_utils import get_statefulsets_managed_by_mindworld, scale_statefulset, create_or_update_statefulset_and_service
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    return render(request, 'dashboard/dashboard.html')

@login_required
def nodes(request):
    return render(request, 'dashboard/nodes.html')

@login_required
def create_server(request):
    if request.method == "POST":
        form = CreateServerForm(request.POST)
        if form.is_valid():
            server_name = form.cleaned_data['serverName']
            env_vars = {
                "EULA": "TRUE" if form.cleaned_data['eula'] else "FALSE",
                "MEMORY": str(form.cleaned_data['memory']),
                "MAX_PLAYERS": str(form.cleaned_data['maxPlayers'])
            }
            try:
                create_or_update_statefulset_and_service(server_name, env_vars)
                return redirect('home')  # Redirect to home or a success page after creating the server
            except Exception as e:
                return HttpResponse(f"Error: {str(e)}", status=500)
    else:
        form = CreateServerForm()

    return render(request, 'dashboard/create_server.html', {'form': form})

@login_required
def start_server(request, namespace, name):
    scale_statefulset(namespace, name, replicas=1)
    return redirect('home')

@login_required
def stop_server(request, namespace, name):
    scale_statefulset(namespace, name, replicas=0)
    return redirect('home')

@login_required
def restart_server(request, namespace, name):
    scale_statefulset(namespace, name, replicas=0)
    scale_statefulset(namespace, name, replicas=1)
    return redirect('home')

@login_required
def get_server_status(request):
    servers = get_statefulsets_managed_by_mindworld()
    return JsonResponse(servers, safe=False)

@login_required
def edit_server(request, namespace, name):
    context = {
        'namespace': namespace,
        'deployment_name': name,
    }
    return render(request, 'dashboard/edit_server.html', context)

@login_required
def manage_server(request, namespace, name, action):
    if request.method == 'POST':
        if action == 'start':
            scale_statefulset(namespace, name, replicas=1)
        elif action == 'stop':
            scale_statefulset(namespace, name, replicas=0)
        elif action == 'restart':
            scale_statefulset(namespace, name, replicas=0)
            scale_statefulset(namespace, name, replicas=1)
        return JsonResponse({'status': 'success', 'action': action})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)