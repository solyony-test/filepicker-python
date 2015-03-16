import mimetypes
import json

import requests

from filepicker_file import FilepickerFile

class FilepickerClient(object):

    API_URL = 'https://www.filepicker.io/api'

    def __init__(self, api_key=None, store='S3', debug=False):
        self.set_api_key(api_key)
        self.set_store(store)

        self.debug = debug

    def set_api_key(self, api_key):
        self.api_key = api_key

    def set_store(self, store):
        self.store = store

    def store_from_url(self, url, store=None, **kwargs):
        params = {'url': url}
        if kwargs:
            params.update(kwargs)
        return self.__post(store, params)

    def store_local_file(self, filepath, store=None, **kwargs):
        files = {'fileUpload': open(filepath, 'rb')}
        params = {'mimetype': mimetypes.guess_type(filepath)}
        if kwargs:
            params.update(kwargs)
        return self.__post(store, params, files)

    def __post(self, store, params, files=None):
        store = store or self.store
        post_url = '{}/store/{}'.format(self.API_URL, store)
        params['key'] = self.api_key
        response = requests.post(post_url, params=params, files=files)
        try:
            response_dict = json.loads(response.text)
            return FilepickerFile(response_dict=response_dict,
                                  api_key=self.api_key)
        except ValueError:
            return response

    def __debug_msg(self, msg):
        if self.debug:
            print msg

