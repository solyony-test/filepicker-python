import mimetypes
import json
import re
import hmac
import hashlib
import base64

import requests


class FilepickerFile(object):

    FILE_API_URL = 'https://www.filepicker.io/api/file/'

    def __init__(self, handle=None, url=None, response_dict=None,
                 api_key=None, security_secret=None, **kwargs):

        self.metadata = None
        self.converted = kwargs.get('converted', False)
        self.policies = {}
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

    def delete(self):
        """
        Delete file. Returns requests.Response object.
        """
        if self.api_key is None:
            return "Please set API key first"
        return requests.delete(self.url + '?key=' + self.api_key)

    def download(self, destination_path):
        with open(destination_path, 'wb') as f:
            response = requests.get(self.url, stream=True)
            if response.ok:
                for chunk in response.iter_content(1024):
                    if not chunk:
                        break
                    f.write(chunk)
            return response

    def overwrite(self, url=None, path=None):
        data, files = None, None
        if url:
            data = {'url': url}
        if path:
            files = {'fileUpload': open(path, 'rb')}
            data = {'mimetype': mimetypes.guess_type(path)}
        return self.__post(self.url, data=data, files=files)

    def convert(self, **options):
        storing_options = ['filename', 'storeLocation', 'storePath',
                           'storeContainer', 'storeAccess']

        conversions = ['w', 'h', 'fit', 'crop', 'allign', 'format',
                       'filter', 'blurAmount', 'sharpenAmount',
                       'compress', 'quality', 'rotate',
                       'watermark', 'watersize', 'waterposition']
        c_opts = []
        for c in conversions:
            if options.get(c, False):
                c_opts.append('{}={}'.format(c, options[c]))

        s_opts = []
        for o in storing_options:
            if options.get(o, False):
                s_opts.append('{}={}'.format(o, options[o]))

        if s_opts:
            if self.api_key is None:
                return "Please set API key first"
            url = '{}/convert?{}&{}?key={}'.format(self.url, '&'.join(c_opts),
                               '&'.join(s_opts), self.api_key)
            return self.__post(url)
        url = '{}/convert?{}'.format(self.url, '&'.join(c_opts))
        return FilepickerFile(url=url, converted=True)

    def add_policy(self, name, policy):
        self.policies[name] = policy

    def get_auth_url(self, policy_name):
        json_policy = json.dumps(self.policies[policy_name])
        policy = base64.urlsafe_b64encode(json_policy)
        signature = hmac.new(self.security_secret, policy,
                             hashlib.sha256).hexdigest()
        return self.url + '?signature={}&policy={}'.format(signature, policy)


    def __post(self, url, **kwargs):
        try:
            r = requests.post(url,
                              data=kwargs.get('data'),
                              files=kwargs.get('files'))
            rd = json.loads(r.text)
            return FilepickerFile(response_dict=rd, api_key=self.api_key)
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

