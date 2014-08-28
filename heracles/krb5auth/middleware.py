from django.contrib.auth.middleware import RemoteUserMiddleware
from django.contrib.auth import logout
from django.http import HttpResponseRedirect

from mediakrb import kerberos
from . import utils

from urllib import quote

class LimitedRemoteUserMiddleware(RemoteUserMiddleware):
    '''
    Same behaviour as RemoteUserMiddleware except that it doesn't logout user
    if they are already logged in.
    Ueful when you have just one authentication powered login page.
    '''
    def process_request(self, request):
        if not hasattr(request, 'user') or not request.user.is_authenticated():
            super(LimitedRemoteUserMiddleware, self).process_request(request)
        else:
            if not self.validate_credential_cache(request.user.username, request.user.credential_cache_path):
                logout(request)
                del request.user

    def validate_credential_cache(self, principal, credential_cache_path):
        server_principal = utils.build_server_principal()
        kauth = utils.build_kauth(server_principal)
        user_principal = kerberos.KerberosPrincipal(principal, ccache=credential_cache_path)
        return kauth.is_logged_in(user_principal)

class RequireLoginMiddleware(object):
    def __init__(self):
        self.login_path = '/auth/login/'

    def process_request(self, request):
        if request.path != self.login_path and request.user.is_anonymous():
            return HttpResponseRedirect('%s?next=%s' % (self.login_path, quote(request.path)))
