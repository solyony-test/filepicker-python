import mimetypes
import json
import re
import hmac
import hashlib
import base64
import urllib

import requests


class FilepickerFile(object):

    FILE_API_URL = 'https://www.filepicker.io/api/file/'

    def __init__(self, handle=None, url=None, response_dict=None,
                 api_key=None, security_secret=None, policies={},
                 **kwargs):

        self.metadata = None
        self.converted = kwargs.get('converted', False)
        self.policies = policies
        if handle:
            self.__init_with_handle_or_url(handle=handle)
        elif url:
            self.__init_with_handle_or_url(url=url)
        elif response_dict:
            self.__init_with_dict(response_dict)
        else:
            raise AttributeError('Please provide file handle or url')

        self.handle = handle if handle else self.__get_handle()
        self.set_api_key(api_key)
        self.set_security_secret(security_secret)

    #def __str__(self):
    #    return self.url

    def __init_with_dict(self, d):
        if self.converted:
            return
        for key in d:
            self.__setattr__(key, d[key])

    def __init_with_handle_or_url(self, handle=None, url=None):
        if handle:
            self.url = self.FILE_API_URL + handle
        elif url:
            self.url = url
        self.update_metadata()
        self.__init_with_dict(self.metadata)

    def __get_handle(self):
        return re.search(r'file/(\w+)', self.url).group(1)

    def set_api_key(self, api_key):
        """
        Set API key for FilepickerFile object
        """
        self.api_key = api_key

    def set_security_secret(self, secret):
        """
        Set security secret for FilepickerFile object
        """
        self.security_secret = secret

    def update_metadata(self):
        response = requests.get(self.url + '/metadata')
        try:
            self.metadata = json.loads(response.text)
        except ValueError:
            self.metadata = {}

    def delete(self, policy_name=None):
        """
        Delete file. Returns requests.Response object.
        """
        if self.api_key is None:
            return "Please set API key first"
        params = {'key': self.api_key}
        if policy_name:
            params.update(self.__signature_params(policy_name))
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
        params, files = None, None
        if url:
            params = {'url': url}
        if filepath:
            files = {'fileUpload': open(filepath, 'rb')}
            params = {'mimetype': mimetypes.guess_type(filepath)}
        if policy_name:
            params.update(self.__signature_params(policy_name))
        return self.__post(self.url, files=files, params=params)

    def convert(self, policy_name=None, **kwargs):
        if self.converted:
            return "File already converted"

        storing_options = ['filename', 'storeLocation', 'storePath',
                           'storeContainer', 'storeAccess']
        if policy_name:
            kwargs.update(self.__signature_params(policy_name))

        if set(storing_options) & set(kwargs.keys()):
            if self.api_key is None:
                return "Please set API key first"
            kwargs['key'] = self.api_key
            return self.__post(self.url + '/convert', params=kwargs)

        url = requests.get(self.url + '/convert', params=kwargs).url
        return FilepickerFile(url=url, converted=True)

    def add_policy(self, name, policy):
        if policy.get('handle'):
            policy.pop('handle')
        self.policies[name] = policy

    def get_signed_url(self, policy_name):
        params = self.__signature_params(policy_name)
        return self.url + '?' + urllib.urlencode(params)

    def __signature_params(self, policy_name):
        policy = self.policies[policy_name].copy()
        policy['handle'] = self.handle
        json_policy = json.dumps(self.policies[policy_name])
        policy_enc = base64.urlsafe_b64encode(json_policy)
        signature = hmac.new(self.security_secret, policy_enc,
                             hashlib.sha256).hexdigest()
        return {'signature': signature, 'policy': policy}

    def __post(self, url, files=None, **kwargs):
        try:
            r = requests.post(url, files=files, params=kwargs.get('params'))
            rd = json.loads(r.text)
            return FilepickerFile(
                    response_dict=rd, api_key=self.api_key,
                    security_secret=self.security_secret,
                    policies=self.policies)
        except requests.exceptions.ConnectionError as e:
            raise e

    def __getattribute__(self, name):
        CASHABLE_ATTRS = ['metadata']
        if name in CASHABLE_ATTRS:
            value = super(FilepickerFile, self).__getattribute__(name)
            if value is None:
                self.update_metadata()
                return  super(FilepickerFile, self).__getattribute__(name)
            else:
                return value
        return super(FilepickerFile, self).__getattribute__(name)

