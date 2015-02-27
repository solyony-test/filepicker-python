import requests
import mimetypes
import json

from filepicker_file import FilepickerFile

class Filepicker(object):

    API_URL = 'https://www.filepicker.io/api'

    def __init__(self, api_key=None, store='S3', debug=False):
        self.set_api_key(api_key)
        self.set_store(store)

        self.debug = debug

    def set_api_key(self, api_key):
        self.api_key = api_key

    def set_store(self, store):
        self.store = store

    def store_from_url(self, url, **kwargs):
        data = {'url': url}
        store = kwargs.get('store', self.store)
        return self.__post(store, data=data)

    def store_local_file(self, filepath, **kwargs):
        files = {'fileUpload': open(filepath, 'rb')}
        payload = {'mimetype': mimetypes.guess_type(filepath)}
        store = kwargs.get('store', self.store)
        return self.__post(store, data=payload, files=files)

    def __post(self, store, **post_data):
        post_url = "%s/store/%s?key=%s" % (self.API_URL, store, self.api_key)

        self.__debug_msg('Post URL: %s\nPOST data: %s' % \
                (post_url, post_data))

        response = requests.post(
                       post_url,
                       data = post_data.get('data', None),
                       files = post_data.get('files', None)
                   )
        try:
            response_dict = json.loads(response.text)
            return FilepickerFile(response_dict)
        except ValueError:
            return response

    def __debug_msg(self, msg):
        if self.debug:
            print msg

