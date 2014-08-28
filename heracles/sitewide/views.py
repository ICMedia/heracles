from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth import logout as dca_logout, authenticate as dca_authenticate, login as dca_login

# Create your views here.
def frontpage(request):
    return render(request, 'sitewide/index.html')

def logout(request):
    dca_logout(request)
    return HttpResponseRedirect('/auth/login/')

def login(request):
    dest = request.GET.get('next', None)
    if not dest or not dest.startswith('/') or dest.startswith('//'):
        dest = '/'

    if request.user.is_authenticated():
        return HttpResponseRedirect(dest)

    attempted = False

    if request.method == 'POST':
        un, pw = request.POST.get('username', None), request.POST.get('password', None)
        attempted = True
        user = dca_authenticate(username=un, password=pw)
        if user is not None:
            if user.is_active:
                dca_login(request, user)
                return HttpResponseRedirect(dest)

    return render(request, 'sitewide/login.html', {'attempted': attempted})
