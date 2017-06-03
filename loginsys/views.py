# -*- coding: utf-8 -*-

from django.shortcuts import redirect, render_to_response
from django.contrib import auth
from django.core.context_processors import csrf
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.hashers import check_password
from DataManager import DataManager
from django.contrib.auth.models import User

def login(request):
    args={}
    args.update(csrf(request))
    if request.POST:
        username = request.POST.get('username','')
        password = request.POST.get('password','')
        user = auth.authenticate(username=username,password=password)
        if user is not None:
            auth.login(request,user)
            return redirect('/')
        with DataManager() as dm:
            hash = dm.get_password(username)
            isTeacher = dm.isTeacher(username)
        if check_password(password,hash):
            user = User.objects.create_user(username=username,password=password)
            user.is_active=isTeacher
            user.save()
            user = auth.authenticate(username=username,password=password)
            auth.login(request,user)
            return redirect('/')
        else:
            args['login_error'] = 'Користувач не знайдений'
            return render_to_response('login.html',args)
    else:
        return render_to_response('login.html',args)

def logout(request):
    user = User.objects.get(username=request.user)
    auth.logout(request)
    if not user.is_staff:
        user.delete()
    return redirect('/')

def register(request):
    print 'in register'
    args = {}
    args.update(csrf(request))
    args['form'] = UserCreationForm
    if request.POST:
        newuser_form = UserCreationForm(request.POST)
        if newuser_form.is_valid():
            newuser_form.save()
            newuser = auth.authenticate(username=newuser_form.cleaned_data['username'],password=newuser_form.cleaned_data['password2'])
            auth.login(request,newuser)
            return redirect('/')
        else:
            args['form'] = newuser_form
    return render_to_response('register.html',args)