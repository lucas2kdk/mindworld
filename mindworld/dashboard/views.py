import os
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .forms import CreateServerForm
from .server_utils import get_statefulsets_managed_by_mindworld, scale_statefulset, create_or_update_statefulset_and_service

def home(request):
    return render(request, 'dashboard/dashboard.html')

def user_signup(request):
    return render(request, 'dashboard/signup.html')

def user_login(request):
    return render(request, 'dashboard/login.html')

def nodes(request):
    return render(request, 'dashboard/nodes.html')

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

def start_server(request, namespace, name):
    scale_statefulset(namespace, name, replicas=1)
    return redirect('home')

def stop_server(request, namespace, name):
    scale_statefulset(namespace, name, replicas=0)
    return redirect('home')

def restart_server(request, namespace, name):
    scale_statefulset(namespace, name, replicas=0)
    scale_statefulset(namespace, name, replicas=1)
    return redirect('home')

def get_server_status(request):
    servers = get_statefulsets_managed_by_mindworld()
    return JsonResponse(servers, safe=False)

def edit_server(request, namespace, name):
    context = {
        'namespace': namespace,
        'deployment_name': name,
    }
    return render(request, 'dashboard/edit_server.html', context)

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