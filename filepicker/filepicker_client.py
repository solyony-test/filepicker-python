import mimetypes
import json
import os

import requests

from .filepicker_file import FilepickerFile
from .filepicker_policy import FilepickerPolicy


class FilepickerClient(object):

    API_URL = 'https://www.filepicker.io/api'

    def __init__(self, api_key=None, storage='S3', app_secret=None):
        self.set_api_key(api_key)
        self.set_storage(storage)
        self.set_app_secret(app_secret)
        self.policies = {}

    def set_api_key(self, api_key):
        self.api_key = api_key

    def set_storage(self, storage):
        self.storage = storage

    def set_app_secret(self, secret):
        self.app_secret = secret

    def store_from_url(self, url, storage=None, policy_name=None, **kwargs):
        params = {}
        data = {'url': url}
        if policy_name:
            params.update(self.policies[policy_name].signature_params())
        if kwargs:
            params.update(kwargs)
        return self.__post(storage, data=data, params=params)

    def store_local_file(self, filepath, storage=None,
                         policy_name=None, **kwargs):
        filename = os.path.basename(filepath)
        mimetype = mimetypes.guess_type(filepath)
        files = {'fileUpload': (filename, open(filepath, 'rb'), mimetype)}
        params = {}
        if policy_name:
            params.update(self.policies[policy_name].signature_params())
        if kwargs:
            params.update(kwargs)
        return self.__post(storage, files=files, params=params)

    def add_policy(self, name, policy):
        if self.app_secret is None:
            raise Exception("Please set app secret first")
        self.policies[name] = FilepickerPolicy(policy, self.app_secret)

    def __post(self, storage, data=None, files=None, params=None):
        storage = storage or self.storage
        post_url = '{}/store/{}'.format(self.API_URL, storage)
        params['key'] = self.api_key
        response = requests.post(post_url, data=data, files=files,
                                 params=params)
        try:
            response_dict = json.loads(response.text)
            return FilepickerFile(response_dict=response_dict,
                                  api_key=self.api_key,
                                  app_secret=self.app_secret,
                                  policies=self.policies)
        except ValueError:
            return response
