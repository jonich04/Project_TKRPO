from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout

from server.forms import LoginForm, AccountRegisterForm
from server.models import Account, Action
from server import views
from server import logger


def setup_view(request):
    if Account.objects.all().count() > 0:
        request.session['alert_success'] = "Setup has already been completed."
        return HttpResponseRedirect('/')
    # Get template data from the session
    template_data = views.parse_session(request,{'form_button':"Register"})
    # Proceed with rest of the view
    if request.method == 'POST':
        form = AccountRegisterForm(request.POST)
        if form.is_valid():
            views.register_user(
                form.cleaned_data['email'],
                form.cleaned_data['password_first'],
                form.cleaned_data['firstname'],
                form.cleaned_data['lastname'],
                Account.ACCOUNT_ADMIN
            )
            user = authenticate(
                username=form.cleaned_data['email'].lower(),  # Make sure it's lowercase
                password=form.cleaned_data['password_first']
            )
            logger.log(Action.ACTION_ACCOUNT, "Account login", user.account)
            login(request, user)
            request.session['alert_success'] = "Successfully setup Virtual Clinic's primary admin account."
            return HttpResponseRedirect('/profile/')
    else:
        form = AccountRegisterForm()
    template_data['form'] = form
    return render(request,'virtualclinic/setup.html',template_data)


from django.contrib.auth import logout
from django.http import HttpResponseRedirect
import logging

# Убедитесь, что используется стандартный логгер Django
logger = logging.getLogger(__name__)

def logout_view(request):
    if request.user.is_authenticated:
        # Проверка на наличие связанного аккаунта
        if hasattr(request.user, 'account'):
            logger.log(Action.ACTION_ACCOUNT, "Account logout", request.user.account)
        else:
            # Используем стандартный уровень логирования, если warning не определен
            logger.log(logging.WARNING, "Попытка выхода пользователя без аккаунта")

        # Сохраняем текущие алерты из сессии
        saved_data = {}
        if 'alert_success' in request.session:
            saved_data['alert_success'] = request.session['alert_success']
        else:
            saved_data['alert_success'] = "Вы успешно вышли из системы."
        
        if 'alert_danger' in request.session:
            saved_data['alert_danger'] = request.session['alert_danger']
        
        # Выход пользователя
        logout(request)
        
        # Восстанавливаем алерты после очистки сессии
        request.session.update(saved_data)

    return HttpResponseRedirect('/')



def login_view(request):
    # Authentication check. Users currently logged in cannot view this page.
    if request.user.is_authenticated:
        return HttpResponseRedirect('/profile/')
    elif Account.objects.all().count() == 0:
        return HttpResponseRedirect('/setup/')
    # get template data from session
    template_data = views.parse_session(request,{'form_button':"Вход"})
    # Proceed with the rest of view
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username = form.cleaned_data['email'].lower(),
                password = form.cleaned_data['password']
            )
            userInfo = Account.objects.get(user=user)
            if userInfo.archive == False:
                login(request,user)
                logger.log(Action.ACTION_ACCOUNT,"Вход в аккаунт",request.user.account)
                request.session['alert_success'] = "Вы успешно вошли ."
                return HttpResponseRedirect('/profile/')
            else:
                request.session['alert_danger'] = "Такого аккаунта нет, создайте новый"
                return HttpResponseRedirect('/register/')
    else:
        form = LoginForm()
    template_data['form'] = form
    return render(request, 'virtualclinic/login.html', template_data)


def register_view(request):
    # Authentication check. Users logged in cannot view this page.
    if request.user.is_authenticated:
        return HttpResponseRedirect('/profile/')
    elif Account.objects.all().count() == 0:
        return HttpResponseRedirect('/setup/')
    # Get template data from session
    template_data = views.parse_session(request, {'form_button': "Регистрация"})
    # Proceed with rest of the view
    if request.method == 'POST':
        form = AccountRegisterForm(request.POST)
        if form.is_valid():
            views.register_user(
                form.cleaned_data['email'],
                form.cleaned_data['password_first'],
                form.cleaned_data['firstname'],
                form.cleaned_data['lastname'],
                # form.cleaned_data['speciality'],
                Account.ACCOUNT_PATIENT
            )
            user = authenticate(
                username = form.cleaned_data['email'].lower(),
                password = form.cleaned_data['password_first']
            )
            logger.log(Action.ACTION_ACCOUNT, "Account Login", user.account)
            login(request,user)
            request.session['alert_success'] = "Вы успешно зарегестрировались"
            return HttpResponseRedirect('/profile/')
    else:
        form = AccountRegisterForm()
    template_data['form'] = form
    return render(request,'virtualclinic/register.html',template_data)

def error_denied_view(request):
    # Authentication check
    authentication_result = views.authentication_check(request)
    if authentication_result is not None:
        return authentication_result
    # Get template data from session
    template_data = views.parse_session(request)
    # Proceed with rest of the view
    return render(request,'virtualclinic/error/denied.html',template_data)