# minecraft/views.py

from django.shortcuts import render
from django.http import JsonResponse
from .forms import CommandForm
from .kube import execute_command, load_kube_config, get_kubernetes_client

def command_view(request):
    load_kube_config()
    v1 = get_kubernetes_client()
    if request.method == 'POST':
        form = CommandForm(request.POST)
        if form.is_valid():
            command = form.cleaned_data['command']
            try:
                response = execute_command(v1, command)
                return JsonResponse({'status': 'success', 'output': response})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        form = CommandForm()
    return render(request, 'minecraft/command.html', {'form': form})

def console_view(request):
    return render(request, 'minecraft/console.html')
