import requests
import json
import re


class FilepickerFile(object):

    FILE_API_URL = 'https://www.filepicker.io/api/file/'

    def __init__(self, handle=None, url=None, response_dict=None, api_key=None):
        self.metadata = None
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

    #def __str__(self):
    #    return self.url

    def __init_with_dict(self, d):
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
        h = re.search(r'file/(\w+)', self.url).group(1)
        return h

    def set_api_key(self, api_key):
        self.api_key = api_key

    def update_metadata(self):
        response = requests.get(self.url + '/metadata')
        try:
            self.metadata = json.loads(response.text)
            return True
        except ValueError:
            return False

    def delete(self):
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

