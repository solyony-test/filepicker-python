import unittest2
import json
import hmac
import hashlib
import base64
import os

try:
    import urllib.parse as urllib
except ImportError:
    import urllib

from httmock import urlmatch, HTTMock, all_requests
import requests

from filepicker import FilepickerPolicy, FilepickerFile, FilepickerClient


class FilepickerPolicyTest(unittest2.TestCase):

    FILEHANDLE = 'eyJleHBYYYYYYYYYNTA4MTQxNTXXXX'
    APP_SECRET = 'ABCABCABCABC123123123123XX'

    def setUp(self):
        self.policy = FilepickerPolicy(
                policy={'handle': self.FILEHANDLE, 'expiry': 1508141504},
                app_secret=self.APP_SECRET)

    def test_signature_params(self):
        p = {'handle': self.FILEHANDLE, 'expiry': 1508141504}
        json_p = json.dumps(p)
        expected_policy = base64.urlsafe_b64encode(json_p.encode('utf-8'))
        expected_signature = hmac.new(self.APP_SECRET.encode('utf-8'),
                                      expected_policy,
                                      hashlib.sha256).hexdigest()
        params = self.policy.signature_params()

        self.assertEqual(params['signature'], expected_signature)
        self.assertEqual(params['policy'], expected_policy)


class FilepickerClientTest(unittest2.TestCase):

    UPLOADED_FILE = {
        'url': "https://www.filepicker.io/api/file/hx6uhrXXXXXPIiWvl",
        'size': 8811,
        'type': 'image/jpg',
        'filename': 'awesome.jpg'}

    def setUp(self):
        self.client = FilepickerClient(api_key='SECRET_API_KEY')

    def test_api_key(self):
        self.assertEqual(self.client.api_key, 'SECRET_API_KEY')

    def test_default_storage(self):
        self.assertEqual(self.client.storage, 'S3')

    def test_set_storage(self):
        self.assertEqual(self.client.storage, 'S3')
        self.client.set_storage('Azure')
        self.assertEqual(self.client.storage, 'Azure')

    def test_default_app_secret(self):
        self.assertEqual(self.client.app_secret, None)

    def test_set_app_secret(self):
        self.client.set_app_secret('FooBarBaz')
        self.assertEqual(self.client.app_secret, 'FooBarBaz')

    def test_store_from_url(self):

        @urlmatch(netloc=r'www\.filepicker\.io', path='/api', method='post',
                  scheme='https')
        def api_url(url, request):
            return {'status_code': 200,
                    'content': json.dumps(self.UPLOADED_FILE).encode('utf-8')}

        with HTTMock(api_url):
            file = self.client.store_from_url('filepicker.com/awesome.jpg')

        self.assertIsInstance(file, FilepickerFile)
        self.assertEqual(file.url, self.UPLOADED_FILE['url'])
        self.assertEqual(file.size, self.UPLOADED_FILE['size'])
        self.assertEqual(file.mimetype, self.UPLOADED_FILE['type'])
        self.assertEqual(file.filename, self.UPLOADED_FILE['filename'])

    def test_store_local_file(self):

        @urlmatch(netloc=r'www\.filepicker\.io', path='/api', method='post',
                  scheme='https')
        def api_url(url, request):
            return {'status_code': 200,
                    'content': json.dumps(self.UPLOADED_FILE).encode('utf-8')}

        with HTTMock(api_url):
            file = self.client.store_local_file(__file__)

        self.assertIsInstance(file, FilepickerFile)
        self.assertEqual(file.url, self.UPLOADED_FILE['url'])
        self.assertEqual(file.size, self.UPLOADED_FILE['size'])
        self.assertEqual(file.mimetype, self.UPLOADED_FILE['type'])
        self.assertEqual(file.filename, self.UPLOADED_FILE['filename'])

    def test_storage_param(self):
        @urlmatch(netloc=r'www\.filepicker\.io', path='/api', method='post',
                  scheme='https')
        def api_url(url, request):
            if 'default.jpg' in request.body:
                self.assertEqual(url.path, '/api/store/S3')
            else:
                self.assertEqual(url.path, '/api/store/azure')
            content = json.dumps(self.UPLOADED_FILE)
            return { 'status_code': 200, 'content': content}

        with HTTMock(api_url):
            self.client.store_from_url('example.com/default.jpg')
            self.client.store_from_url('example.com/another.jpg',
                                       storage='azure')

    def test_add_policy(self):
        self.assertEqual(len(self.client.policies), 0)
        self.assertIsNone(self.client.app_secret)
        self.assertRaises(Exception,
                          self.client.add_policy, 'zz', {'expiry': 1})

        self.client.set_app_secret("SECRET")
        self.client.add_policy('newpolicy', {'expiry': 150000000})
        self.assertEqual(len(self.client.policies), 1)

    def test_storing_with_security_enabled(self):

        secured_msg = 'This action has been secured'

        @urlmatch(netloc=r'www\.filepicker\.io', path='/api', method='post',
                  scheme='https')
        def require_signature(url, request):
            if all(item in url.query for item in ['policy', 'signature']):
                # just checking if policy and signature are added to query
                # string, not the actual value
                content = json.dumps(self.UPLOADED_FILE).encode('utf-8')
                return {
                    'status_code': 200, 'content': content}
            else:
                return {'status_code': 200,
                        'content': secured_msg.encode('utf-8')}

        self.client.set_app_secret('verysecuresecret')

        self.client.add_policy('test_policy', {'expiry': 123})
        with HTTMock(require_signature):
            response = self.client.store_from_url('filepicker.io/test.jpg')

        self.assertIsInstance(response, requests.Response)
        self.assertEqual(response.text, str(secured_msg))

        with HTTMock(require_signature):
            file = self.client.store_from_url('filepicker.io/test.jpg',
                                              policy_name='test_policy')

        self.assertIsInstance(file, FilepickerFile)
        self.assertEqual(file.url, self.UPLOADED_FILE['url'])
        self.assertEqual(file.size, self.UPLOADED_FILE['size'])
        self.assertEqual(file.mimetype, self.UPLOADED_FILE['type'])
        self.assertEqual(file.filename, self.UPLOADED_FILE['filename'])

    def test_key_inheritance(self):
        @urlmatch(netloc=r'www\.filepicker\.io', path='/api', method='post',
                  scheme='https')
        def api_url(url, request):
            # return json.dumps(self.UPLOADED_FILE).encode('utf-8')
            return {'status_code': 200,
                    'content': json.dumps(self.UPLOADED_FILE).encode('utf-8')}

        with HTTMock(api_url):
            file = self.client.store_local_file(__file__)

        self.assertEqual(file.api_key, self.client.api_key)
        self.assertEqual(file.app_secret, self.client.app_secret)

        secret_before = self.client.app_secret
        self.client.set_app_secret('verysecuresecret')
        secret_after = self.client.app_secret

        @urlmatch(netloc=r'www\.filepicker\.io', path='/api', method='post',
                  scheme='https')
        def api_url(url, request):
            # return json.dumps(self.UPLOADED_FILE).encode('utf-8')
            return {'status_code': 200,
                    'content': json.dumps(self.UPLOADED_FILE).encode('utf-8')}

        with HTTMock(api_url):
            file = self.client.store_local_file(__file__)

        self.assertNotEqual(secret_before, secret_after)
        self.assertEqual(file.api_key, self.client.api_key)
        self.assertEqual(file.app_secret, self.client.app_secret)


class FilepickerFileTest(unittest2.TestCase):

    HANDLE = 'XXMadeUpHandleXX'

    def setUp(self):
        self.file = FilepickerFile(handle=self.HANDLE)

    def test_init_with_handle(self):
        self.assertEqual(self.file.handle, self.HANDLE)
        self.assertEqual(self.file.url, self.file.FILE_API_URL + self.HANDLE)
        self.assertEqual(self.file.metadata, {})

    def test_init_with_url(self):
        url = 'https://www.filepicker.io/api/file/{}'.format(self.HANDLE)
        file = FilepickerFile(url=url)

        self.assertEqual(file.url, url)
        self.assertEqual(file.handle, self.HANDLE)
        self.assertEqual(file.metadata, {})

    def test_init_with_dict(self):
        file_dict = {
            'url': "https://www.filepicker.io/api/file/" + self.HANDLE,
            'size': 8811,
            'type': 'image/jpg',
            'filename': 'awesome.jpg'}

        file = FilepickerFile(response_dict=file_dict.copy())
        self.assertEqual(file.url, file_dict['url'])
        self.assertEqual(file.handle, self.HANDLE)
        self.assertNotEqual(file.metadata, None)
        self.assertEqual(file.mimetype, file_dict['type'])

        self.assertRaises(AttributeError,
                          file.__getattribute__, 'non_existent_attr')

    def test_set_api_key(self):
        self.assertEqual(self.file.api_key, None)
        self.file.set_api_key('my_key')
        self.assertEqual(self.file.api_key, 'my_key')

    def test_set_app_secret(self):
        self.assertEqual(self.file.app_secret, None)
        self.file.set_app_secret('my_s')
        self.assertEqual(self.file.app_secret, 'my_s')

    def test_update_metada(self):
        self.assertEqual(self.file.metadata, {})

        @urlmatch(netloc=r'www\.filepicker\.io',
                  path='/api/file/{}/metadata'.format(self.HANDLE),
                  method='get', scheme='https')
        def metadata_url(url, request):
            for attr in self.file.METADATA_ATTRS:
                self.assertIn('{}=true'.format(attr), url.query)
            return {'status_code': 200,
                    'content': json.dumps({'md5': '123abc'}).encode('utf-8')}

        with HTTMock(metadata_url):
            self.file.update_metadata()

        self.assertEqual(self.file.md5, '123abc')

    def test_delete(self):

        @urlmatch(netloc=r'www\.filepicker\.io',
                  path='/api/file/{}'.format(self.HANDLE),
                  method='delete', scheme='https')
        def delete_file(url, request):
            # return 'success'
            return {'status_code': 200, 'content': 'success'.encode('utf-8')}

        self.assertEqual(self.file.api_key, None)
        self.assertEqual(self.file.delete(), 'Please set API key first')

        self.file.set_api_key('key')

        with HTTMock(delete_file):
            response = self.file.delete()

        self.assertIsInstance(response, requests.Response)
        self.assertEqual(response.text, 'success')
        self.assertEqual(response.status_code, 200)

    def test_download(self):
        dest_path = 'delete_this_test_leftover'
        f_content = 'downloaded file content'

        @urlmatch(netloc=r'www\.filepicker\.io',
                  path='/api/file/{}'.format(self.HANDLE),
                  method='get', scheme='https')
        def download_file(url, request):
            return {'status_code': 200, 'content': f_content.encode('utf-8')}
            # return "downloaded file content"

        with HTTMock(download_file):
            self.file.download(dest_path)

        try:
            with open(dest_path) as f:
                self.assertEqual(f.read(), f_content)
            os.remove(dest_path)
        except IOError as e:
            print("Looks like something went wrong: {}".format(e))
            self.assertTrue(False)

    def test_download_with_security_enabled(self):
        dest_path = 'delete_this_test_leftover'
        secured_msg = 'This action has been secured'

        @urlmatch(netloc=r'www\.filepicker\.io',
                  path='/api/file/{}'.format(self.HANDLE),
                  method='get', scheme='https')
        def download_file(url, request):
            if all(item in url.query for item in ['policy', 'signature']):
                # just checking if policy and signature are added to query
                # string, not the actual value
                return {'status_code': 200,
                        'content': 'downloaded file content'.encode('utf-8')}
            return {'status_code': 200,
                    'content': secured_msg.encode('utf-8')}

        with HTTMock(download_file):
            self.file.download(dest_path)  # download with no policy

        try:
            with open(dest_path) as f:
                self.assertEqual(f.read(), secured_msg)
            os.remove(dest_path)
        except IOError as e:
            print("Looks like something went wrong: {}".format(e))
            self.assertTrue(False)

        self.file.set_app_secret("SECRET")
        self.file.add_policy('newpolicy', {'call': 'download', 'expiry': 999})
        with HTTMock(download_file):
            self.file.download(dest_path, policy_name='newpolicy')

        try:
            with open(dest_path) as f:
                self.assertEqual(f.read(), 'downloaded file content')
            os.remove(dest_path)
        except IOError as e:
            print("Looks like something went wrong: {}".format(e))
            self.assertTrue(False)

    def test_overwrite(self):

        @all_requests
        def overwrite_file(url, request):
            self.assertEqual(request.url, self.file.url)
            self.assertEqual(request.method, 'POST')
            self.assertIn(urllib.quote('somenew.url/new.png', ''),
                          request.body)
            j = {"url": "https://www.filepicker.io/api/file/ZXC",
                 "filename": "name.jpg"}
            return {'status_code': 200,
                    'content': json.dumps(j).encode('utf-8')}

        with HTTMock(overwrite_file):
            self.file.overwrite(url='somenew.url/new.png')

        @all_requests
        def overwrite_file(url, request):
            self.assertEqual(request.url, self.file.url)
            self.assertEqual(request.method, 'POST')
            self.assertIn('name="fileUpload"', str(request.body))
            j = {"url": "https://www.filepicker.io/api/file/ZXC",
                 "filename": "name.jpg"}
            return {'status_code': 200,
                    'content': json.dumps(j).encode('utf-8')}

        with HTTMock(overwrite_file):
            self.file.overwrite(filepath=__file__)

    def test_already_converted(self):
        f = FilepickerFile(url="filepicker.io/api/file/ZXC", temporary=True)
        self.assertEqual(f.convert(w=10), 'File already converted')

    def test_convert(self):
        converted_file = self.file.convert(filter='blur', blurAmount=2, w=20)
        self.assertRegexpMatches(converted_file.url, r'convert.+filter=blur')
        self.assertRegexpMatches(converted_file.url, r'convert.+blurAmount=2')
        self.assertRegexpMatches(converted_file.url, r'convert.+w=20')
        self.assertTrue(converted_file.temporary)

    def test_convert_and_store(self):
        self.assertIsNone(self.file.api_key)
        self.assertEqual(self.file.convert(w=10, storeLocation='S3'),
                         'Please set API key first')

        self.file.set_api_key('APIKEY')

        fp_response = {
            "size": 999, "type": "image/jpeg",
            "url": "https://www.filepicker.io/api/file/ZXC",
            "filename": "logo.jpg"}

        @urlmatch(netloc=r'www\.filepicker\.io',
                  path='/api/file/{}/convert'.format(self.HANDLE),
                  method='post', scheme='https')
        def convert_and_store(url, request):
            self.assertIn('w=10', url.query)
            self.assertIn('key=APIKEY', url.query)
            self.assertIn('storeLocation=Azure', url.query)
            return {'status_code': 200,
                    'content': json.dumps(fp_response).encode('utf-8')}

        with HTTMock(convert_and_store):
            converted_file = self.file.convert(w=10, storeLocation='Azure')

        self.assertFalse(converted_file.temporary)
        self.assertEqual(converted_file.url, fp_response['url'])
        self.assertEqual(converted_file.handle, 'ZXC')

    def test_key_inheritance(self):
        self.file.set_api_key('APIKEY')
        converted_file = self.file.convert(filter='blur', blurAmount=2, w=20)
        self.assertEqual(self.file.api_key, converted_file.api_key)
        self.assertEqual(self.file.app_secret, converted_file.app_secret)
        self.assertEqual(self.file.policies, converted_file.policies)

        fp_response = {
            "size": 999, "type": "image/jpeg",
            "url": "https://www.filepicker.io/api/file/ZXC",
            "filename": "logo.jpg"}

        @urlmatch(netloc=r'www\.filepicker\.io',
                  path='/api/file/{}/convert'.format(self.HANDLE),
                  method='post', scheme='https')
        def convert_and_store(url, request):
            return {'status_code': 200,
                    'content': json.dumps(fp_response).encode('utf-8')}

        secret_before = self.file.app_secret
        self.file.set_app_secret('APPSECRET')
        secret_after = self.file.app_secret

        self.file.add_policy('foo', {'expiry': 15})
        with HTTMock(convert_and_store):
            converted_file = self.file.convert(w=10, storeLocation='Azure')

        self.assertIn('foo', converted_file.policies)
        self.assertNotEqual(secret_before, secret_after)
        self.assertEqual(self.file.app_secret, converted_file.app_secret)
        self.assertEqual(self.file.api_key, converted_file.api_key)

    def test_add_policy(self):
        self.assertTrue(len(self.file.policies) == 0)
        self.assertIsNone(self.file.app_secret)
        self.assertRaises(Exception,
                          self.file.add_policy, 'zz', {'expiry': 1})

        self.file.set_app_secret('sec')
        self.file.add_policy('new_policy', {'expiry': 1, 'call': 'read'})
        self.assertTrue(len(self.file.policies) == 1)

    def test_signed_url(self):
        self.file.set_app_secret('sec')
        self.file.add_policy('new_policy', {'expiry': 1, 'call': 'read'})
        url = self.file.get_signed_url('new_policy')
        self.assertRegexpMatches(
                url,
                r'{}.+signature.+'.format(self.file.url))
        self.assertRegexpMatches(
                url,
                r'{}.+policy.+'.format(self.file.url))


if __name__ == '__main__':
    unittest2.main()
