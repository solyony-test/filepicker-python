import mimetypes
import json
import re
import os

try:
    import urllib.parse as parser
except ImportError:
    import urllib as parser

import requests

from .filepicker_policy import FilepickerPolicy


class FilepickerFile(object):

    FILE_API_URL = 'https://www.filepicker.io/api/file/'
    METADATA_ATTRS = ['size', 'mimetype', 'filename', 'width',
                      'height', 'uploaded', 'writeable', 'md5',
                      'location', 'path', 'container', 'key']

    def __init__(self, handle=None, url=None, response_dict=None,
                 api_key=None, app_secret=None, policies={},
                 **kwargs):

        self.metadata = None
        self.temporary = kwargs.get('temporary', False)

        if handle:
            self.__init_with_handle_or_url(handle=handle)
        elif url:
            self.__init_with_handle_or_url(url=url)
        elif response_dict:
            self.__init_with_dict(response_dict)
        else:
            raise AttributeError('Please provide file handle or url')

        self.policies = policies
        self.handle = handle if handle else self.__get_handle()
        self.set_api_key(api_key)
        self.set_app_secret(app_secret)

    def __init_with_dict(self, d):
        self.url = d['url']
        if d.get('type'):
            d['mimetype'] = d.pop('type')
            self.metadata = d

    def __init_with_handle_or_url(self, handle=None, url=None):
        if handle:
            self.url = self.FILE_API_URL + handle
        elif url:
            self.url = url
        self.metadata = {}

    def __get_handle(self):
        try:
            return re.search(r'file/(\w+)', self.url).group(1)
        except AttributeError:
            raise Exception("Invalid file url")

    def set_api_key(self, api_key):
        self.api_key = api_key

    def set_app_secret(self, secret):
        self.app_secret = secret

    def update_metadata(self, policy_name=None):
        params = dict((x, 'true') for x in self.METADATA_ATTRS)
        if policy_name:
            params.update(self.policies[policy_name].signature_params())
        response = requests.get(self.url + '/metadata', params=params)
        try:
            self.metadata = json.loads(response.text)
        except ValueError:
            self.metadata = {}

    def delete(self, policy_name=None):
        if self.api_key is None:
            return "Please set API key first"
        params = {'key': self.api_key}
        if policy_name:
            params.update(self.policies[policy_name].signature_params())
        return requests.delete(self.url, params=params)

    def download(self, destination_path, policy_name=None):
        url = self.get_signed_url(policy_name) if policy_name else self.url
        with open(destination_path, 'wb') as f:
            response = requests.get(url, stream=True)
            if response.ok:
                for chunk in response.iter_content(1024):
                    if not chunk:
                        break
                    f.write(chunk)
            return response

    def overwrite(self, url=None, filepath=None, policy_name=None):
        data, files, params = None, None, None
        if url:
            data = {'url': url}
        if filepath:
            filename = os.path.basename(filepath)
            mimetype = mimetypes.guess_type(filepath)
            files = {'fileUpload': (filename, open(filepath, 'rb'), mimetype)}
        if policy_name:
            params.update(self.policies[policy_name].signature_params())
        return self.__post(self.url, data=data, files=files, params=params)

    def convert(self, policy_name=None, **kwargs):
        if self.temporary:
            return "File already converted"

        storing_options = ['filename', 'storeLocation', 'storePath',
                           'storeContainer', 'storeAccess']
        if policy_name:
            kwargs.update(self.policies[policy_name].signature_params())

        if set(storing_options) & set(kwargs.keys()):
            if self.api_key is None:
                return "Please set API key first"
            kwargs['key'] = self.api_key
            return self.__post(self.url + '/convert', params=kwargs)

        url = '{}/convert?{}'.format(self.url, parser.urlencode(kwargs))
        return FilepickerFile(url=url, api_key=self.api_key,
                              app_secret=self.app_secret,
                              policies=self.policies,
                              temporary=True)

    def add_policy(self, name, policy):
        if self.app_secret is None:
            raise Exception("Please set app secret first")
        self.policies[name] = FilepickerPolicy(policy, self.app_secret)

    def get_signed_url(self, policy_name):
        params = self.policies[policy_name].signature_params()
        return self.url + '?' + parser.urlencode(params)

    def __post(self, url, data=None, files=None, **kwargs):
        try:
            r = requests.post(url, data=data, files=files,
                              params=kwargs.get('params'))
            rd = json.loads(r.text)
            return FilepickerFile(
                    response_dict=rd, api_key=self.api_key,
                    app_secret=self.app_secret,
                    policies=self.policies)
        except requests.exceptions.ConnectionError as e:
            raise e

    def __getattribute__(self, name):
        attrs = super(FilepickerFile, self).__getattribute__('METADATA_ATTRS')
        if name in attrs:
            return super(FilepickerFile, self) \
                      .__getattribute__('metadata').get(name)
        else:
            return super(FilepickerFile, self).__getattribute__(name)
