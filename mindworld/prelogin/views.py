from django.shortcuts import render, redirect
from django.http import HttpResponse
from . forms import UserCreationForm, LoginForm

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import auth

def homepage(request):

    return render(request, "prelogin/index.html")

def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = UserCreationForm()

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()

            return redirect("login")
        
    context = {"registerform": form}
    
    return render(request, "prelogin/register.html", context=context)

def login(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    
    form = LoginForm()

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth.login(request, user)
                return redirect("dashboard")
    
    context = {'loginform':form}
    return render(request, 'prelogin/login.html', context=context)


def user_logout(request):

    auth.logout(request)

    return redirect("")


@login_required(login_url="login")
def dashboard(request):
    
    return render(request, "prelogin/dashboard.html")