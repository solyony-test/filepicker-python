import mimetypes
import json
import os

import requests

from filepicker_file import FilepickerFile
from filepicker_policy import FilepickerPolicy


class FilepickerClient(object):

    API_URL = 'https://www.filepicker.io/api'

    def __init__(self, api_key=None, store='S3', security_secret=None):
        self.set_api_key(api_key)
        self.set_store(store)
        self.set_security_secret(security_secret)
        self.policies = {}

    def set_api_key(self, api_key):
        self.api_key = api_key

    def set_store(self, store):
        self.store = store

    def set_security_secret(self, secret):
        self.security_secret = secret

    def store_from_url(self, url, store=None, policy_name=None, **kwargs):
        params = {}
        data = {'url': url}
        if policy_name:
            params.update(self.policies[policy_name].signature_params())
        if kwargs:
            params.update(kwargs)
        return self.__post(store, data=data, params=params)

    def store_local_file(self, filepath, store=None,
                         policy_name=None, **kwargs):
        filename = os.path.basename(filepath)
        mimetype = mimetypes.guess_type(filepath)
        files = {'fileUpload': (filename, open(filepath, 'rb'), mimetype)}
        params = {}
        if policy_name:
            params.update(self.policies[policy_name].signature_params())
        if kwargs:
            params.update(kwargs)
        return self.__post(store, files=files, params=params)

    def add_policy(self, name, policy):
        if self.security_secret is None:
            raise Exception("Please set security secret first")
        self.policies[name] = FilepickerPolicy(policy, self.security_secret)

    def __post(self, store, data=None, files=None, params=None):
        store = store or self.store
        post_url = '{}/store/{}'.format(self.API_URL, store)
        params['key'] = self.api_key
        response = requests.post(post_url, data=data, files=files,
                                 params=params)
        try:
            response_dict = json.loads(response.text)
            return FilepickerFile(response_dict=response_dict,
                                  api_key=self.api_key,
                                  security_secret=self.security_secret,
                                  policies=self.policies)
        except ValueError:
            return response

