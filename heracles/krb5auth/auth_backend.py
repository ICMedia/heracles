from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.models import Group

from mediakrb import kerberos, ipa
from . import utils

class Krb5RemoteUserBackend(RemoteUserBackend):
    def clean_username(self, username):
        # remove @REALM from username
        return username.split("@")[0]

    def authenticate(self, username=None, password=None, remote_user=None):
        if remote_user is not None:
            return super(Krb5RemoteUserBackend, self).authenticate(remote_user=remote_user)
        elif username is not None and password is not None:
            principal = self.check_user(username, password)
            if principal:
                user = super(Krb5RemoteUserBackend, self).authenticate(remote_user=principal.principal)
                user._dirty = False
                if user.credential_cache_path != principal.ccache:
                    user.credential_cache_path = principal.ccache
                    user._dirty = True
                user._dirty = self.resync(user, principal) or user._dirty
                if user._dirty:
                    user.save()
                return user
        return None

    def resync(self, user, principal):
        principal_data, principal_user_groups = self.get_user_data(principal)

        db_user_groups = set()
        principal_user_groups = set(principal_user_groups)
        group_name_map = {}
        for g in user.groups.all():
            db_user_groups.add(g.name)
            group_name_map[g.name] = g
        if db_user_groups != principal_user_groups:
            remove_from_db = db_user_groups - principal_user_groups
            add_to_db = principal_user_groups - db_user_groups

            if remove_from_db:
                user.groups.remove(*[group_name_map[g] for g in remove_from_db])
            if add_to_db:
                user.groups.add(*[self.make_group(g) for g in add_to_db])
            user._dirty = True

        first_name, last_name = principal_data['result']['givenname'][0], principal_data['result']['sn'][0]
        email = principal_data['result']['mail'][0]
        if user.first_name != first_name:
            user.first_name = first_name
            user._dirty = True
        if user.last_name != last_name:
            user.last_name = last_name
            user._dirty = True
        if user.email != email:
            user.email = email
            user._dirty = True

        return user._dirty

    def make_group(self, name):
        return Group.objects.get_or_create(name=name)[0]

    def get_user_data(self, principal):
        with kerberos.context_principal(principal):
            u_api = ipa.IpaApi().users()
            return u_api.detail(principal.principal), u_api.groups(principal.principal)

    def check_user(self, username, password):
        server_principal = self.build_server_principal()
        kauth = self.build_kauth(server_principal)
        try:
            user_principal = kauth.login(username, password)
            print user_principal, kauth.is_logged_in(user_principal)
            if not kauth.is_logged_in(user_principal):
                return None
            return user_principal
        except:
            return None

    def build_server_principal(self):
        return utils.build_server_principal()

    def build_kauth(self, server_principal):
        return utils.build_kauth(server_principal)
