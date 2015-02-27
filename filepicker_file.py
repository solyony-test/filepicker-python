import requests
import json

class FilepickerFile(object):

    FILE_API_URL = 'https://www.filepicker.io/api/file'

    def __init__(self, response_dict=None, **kwargs):
        self.metadata = None
        if response_dict:
            self.__init_with_dict(response_dict)
        elif 'handle' in kwargs or 'url' in kwargs:
            self.__init_with_handle_or_url(**kwargs)
        else:
            raise TypeError('Please provide response_dict, handle or url')

    def __str__(self):
        return self.url

    def __init_with_dict(self, d):
        for key in d:
            self.__setattr__(key, d[key])

    def __init_with_handle_or_url(self, **kwargs):
        self.url = kwargs.get('url', "%s/%s" % \
                (self.FILE_API_URL, kwargs['handle']))
        self.update_metadata()
        self.__init_with_dict(self.metadata)

    def update_metadata(self):
        response = requests.get(self.url + '/metadata')
        try:
            self.metadata = json.loads(response.text)
            return True
        except ValueError:
            return False

    def delete(self):
        response = requests.delete(self.url)
        return {response['ok'], response['reason']}

    def download(self, destination_path):
        with open(destination_path, 'wb') as f:
            response = requests.get(self.url, stream=True)
            if response.ok:
                for chunk in response.iter_content(1024):
                    if not chunk:
                        break
                    f.write(chunk)
            return {response['ok'], response['reason']}

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

