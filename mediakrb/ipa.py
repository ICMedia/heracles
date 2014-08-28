import ipalib
from threading import local

_saved_data = local()
_saved_data.api = None

class IpaApi(object):
    _saved_data = None

    def __init__(self):
        self._ipa_api = None

    @property
    def ipa_api(self):
        if self._ipa_api is None:
            self._ipa_api = self._make_api()
        return self._ipa_api

    def _make_api(self):
        api = ipalib.api
        try:
            api.bootstrap_with_global_options(context='cli')
            api.load_plugins()
            api.finalize()
        except Exception as ex:
            if str(ex) != 'API.bootstrap() already called':
                raise
        api.Backend.xmlclient.connect()

        return api

    def users(self):
        return IpaUserApi(self)

    @property
    def _cmd(self):
        return self.ipa_api.Command

    @property
    def _base_api(self):
        return self

class IpaSubApi(object):
    def __init__(self, api):
        self.api = api

    @property
    def _cmd(self):
        return self.api._cmd

    @property
    def _base_api(self):
        return self.api._base_api

class IpaUserApi(IpaSubApi):
    def list(self):
        return self._cmd.user_find()

    def list_in_group(self, group):
        return self._cmd.user_find(in_group=unicode(group))

    def list_in_role(self, role):
        return self._cmd.user_find(in_role=unicode(role))

    def detail(self, username):
        return self._cmd.user_show(uid=unicode(username))

    def groups(self, username):
        user = self.detail(username)['result']
        return list(set(user['memberof_group']) | set(user['memberofindirect_group']))

    def roles(self, username):
        user = self.detail(username)['result']
        return list(set(user['memberof_role']) | set(user['memberofindirect_role']))
