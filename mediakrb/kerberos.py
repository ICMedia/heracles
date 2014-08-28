import os
import os.path
import tempfile
from contextlib import contextmanager
from utils import exec_cmd

class LoginException(Exception):
    pass

class PasswordInvalidException(LoginException):
    pass

class PasswordExpiredException(LoginException):
    pass

class AccountLockedException(LoginException):
    pass

class PathDiscoveryException(Exception):
    pass

class ExecutablePathLocator(object):
    COMMANDS = ['kinit', 'kdestroy', 'klist']

    def __init__(self, **kwargs):
        for command in self.COMMANDS:
            setattr(self, command, kwargs.get(command))

    @classmethod
    def autodiscover(cls):
        paths = {}
        for command in cls.COMMANDS:
            paths[command] = cls._autodiscover_path(command)
        return cls(**paths)

    @staticmethod
    def _is_exec(command):
        return os.path.isfile(command) and os.access(command, os.X_OK)

    @classmethod
    def _autodiscover_path(cls, command):
        if cls._is_exec(command):
            return command

        candidate_paths = [path.strip('"') for path in os.environ['PATH'].split(os.pathsep)]

        for candidate_path in candidate_paths:
            candidate_exec = os.path.join(candidate_path, command)
            if cls._is_exec(candidate_exec):
                return candidate_exec

        raise PathDiscoveryException("Failed to locate {} in {}".format(command, ', '.join(candidate_paths)))

class KerberosPaths(ExecutablePathLocator):
    COMMANDS = ['kinit', 'kdestroy', 'klist']

class KerberosPrincipal(object):
    def __init__(self, principal, keytab=None, ccache=None):
        self.principal = principal.split("@")[0]
        self.keytab = keytab
        self.ccache = ccache

class KerberosAuth(object):
    def __init__(self, server_principal, realm, paths=None):
        self.server_principal = server_principal
        self.realm = realm
        self.paths = paths or KerberosPaths.autodiscover()

    def _kinit(self, user_principal, password):
        cc_armor_name = "k5_armor_%s" % (user_principal.principal,)
        cc_armor_path = os.path.join(tempfile.gettempdir(), cc_armor_name)

        # get an armor ccache
        exec_cmd([self.paths.kinit, '-kt', self.server_principal.keytab, self.server_principal.principal], environment={'KRB5CCNAME': cc_armor_path})

        if user_principal.ccache is None:
            cc_user_name = "k5_user_%s" % (user_principal.principal,)
            cc_user_path = os.path.join(tempfile.gettempdir(), cc_user_name)
            user_principal.ccache = cc_user_path

        (stdout, stderr, returncode) = exec_cmd(
            [self.paths.kinit, user_principal.principal, '-T', cc_armor_path],
            environment={'KRB5CCNAME': user_principal.ccache, 'LC_ALL': 'C'},
            stdin=password, raiseonerr=False
        )

        exec_cmd([self.paths.kdestroy, '-A', '-c', cc_armor_path], environment={'KRB5CCNAME': cc_armor_path}, raiseonerr=False)

        if returncode != 0:
            se = stderr.strip()
            if se == 'kinit: Password incorrect while getting initial credentials':
                raise PasswordInvalidException()
            elif se == 'kinit: Cannot read password while getting initial credentials':
                raise PasswordExpiredException()
            elif se == 'kinit: Clients credentials have been revoked while getting initial credentials':
                raise AccountLockedException()
            raise LoginException("Unable to login - got '{}' from kinit".format(se))

        return user_principal

    def _kdestroy(self, user_principal):
        exec_cmd([self.paths.kdestroy, '-A', '-q', '-c', user_principal.ccache], environment={'KRB5CCNAME': user_principal.ccache})

    def _klist(self, user_principal):
        exec_cmd([self.paths.klist, '-c', user_principal.ccache], environment={'KRB5CCNAME': user_principal.ccache})

    def login(self, user, password):
        user_principal = KerberosPrincipal(user)
        return self._kinit(user_principal, password)

    def logout(self, user_principal):
        return self._kdestroy(user_principal)

    def is_logged_in(self, user_principal):
        try:
            self._klist(user_principal)
        except SubprocessFailedException as sfe:
            if sfe.returncode == 1:
                return False
            raise
        return True

@contextmanager
def context_principal(user_principal):
    had_ccache = 'KRB5CCNAME' in os.environ
    old_ccache = os.environ.get('KRB5CCNAME', None)
    os.environ['KRB5CCNAME'] = user_principal.ccache
    my_set_ccache = user_principal.ccache
    yield
    if os.environ.get('KRB5CCNAME', None) == my_set_ccache:
        if had_ccache:
            os.environ['KRB5CCNAME'] = old_ccache
        else:
            del os.environ['KRB5CCNAME']

def set_global_context_principal(user_principal):
    # DON'T DO THIS
    os.environ['KRB5CCNAME'] = user_principal.ccache
