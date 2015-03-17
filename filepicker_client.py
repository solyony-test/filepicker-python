import mimetypes
import json

import requests

from filepicker_file import FilepickerFile
from filepicker_policy import FilepickerPolicy

class FilepickerClient(object):

    API_URL = 'https://www.filepicker.io/api'

    def __init__(self, api_key=None, store='S3', security_secret=None,
                 debug=False):
        self.set_api_key(api_key)
        self.set_store(store)
        self.set_security_secret(security_secret)
        self.policies = {}
        self.debug = debug

    def set_api_key(self, api_key):
        self.api_key = api_key

    def set_store(self, store):
        self.store = store

    def set_security_secret(self, secret):
        """
        Set security secret for FilepickerClient object
        """
        self.security_secret = secret

    def store_from_url(self, url, store=None, policy_name=None, **kwargs):
        params = {'url': url}
        if policy_name:
            params.update(self.policies[policy_name].signature_params())
        if kwargs:
            params.update(kwargs)
        return self.__post(store, params)

    def store_local_file(self, filepath, store=None, policy_name=None, **kwargs):
        files = {'fileUpload': open(filepath, 'rb')}
        params = {'mimetype': mimetypes.guess_type(filepath)}
        if policy_name:
            params.update(self.policies[policy_name].signature_params())
        if kwargs:
            params.update(kwargs)
        return self.__post(store, params, files)

    def add_policy(self, name, policy):
        self.policies[name] = FilepickerPolicy(policy, self.security_secret)

    def __post(self, store, params, files=None):
        store = store or self.store
        post_url = '{}/store/{}'.format(self.API_URL, store)
        params['key'] = self.api_key
        response = requests.post(post_url, params=params, files=files)
        try:
            response_dict = json.loads(response.text)
            return FilepickerFile(response_dict=response_dict,
                                  api_key=self.api_key,
                                  security_secret=self.security_secret,
                                  policies=self.policies)
        except ValueError:
            return response

    def __debug_msg(self, msg):
        if self.debug:
            print msg

