Filepicker Python Library
===================

This module provides an easy way to use [Filepicker's REST API](https://www.filepicker.com/documentation/file_ingestion/rest_api/retrieving) in your Python projects.

# Installation

Install ``filepicker`` with pip:

    $ pip install filepicker

or directly from GitHub

    $ pip install git+https://github.com/filepicker/filepicker-python.git

It will also install `requests` and `httmock` packages.

# How to use it
Filepicker library gives you access to two useful classes:

* `FilepickerClient` - for easy file upload (creates FilepickerFile objects)
* `FilepickerFile` - for file handling (downloading, converting etc.)

## Uploding files
First, you need to create an instance of FilepickerClient

```python
from filepicker import FilepickerClient

client = FilepickerClient(api_key='YOUR_API_KEY')
# or
client = FilepickerClient()
client.set_api_key('YOUR_API_KEY')
```

To store a file from URL

```python
file = client.store_from_url('http://bit.ly/1CzPVQp')
```

To store a file from your hard drive

```python
file = client.store_local_file('/path/to/your/file.jpg')
```

If everything goes well, you will receive a FilepickerFile object. Otherwise, a [requests.Response](http://docs.python-requests.org/en/latest/api/#requests.Response) object will be returned.

When uploading a file, you can also provide additional parameters like the name of the file as it will be stored or indicate that the file should be stored in a way that allows public access:

```python
file = client.store_from_url('http://bit.ly/1CzPVQp', name='final_name.jpg',
                             access='private')
```

Check out [our docs](https://www.filepicker.com/documentation/file_ingestion/rest_api/storing) for more details.

## Storage
Amazon S3 is used to store your files by default. If you wish to use a different one, you can initialize FilepickerClient with an additional `storage` argument or use `set_storage()` method:

```python
client = FilepickerClient(api_key='YOUR_API_KEY', storage='azure')
# or
client = FilepickerClient(api_key='YOUR_API_KEY')
client.set_storage('dropbox')
```

You can also specify storage for a single upload:

```python
client = FilepickerClient(api_key='YOUR_API_KEY') # use S3 by default
file_s3 = client.store_from_url('http://bit.ly/1CzPVQp')
file_azure = client.store_local_file('/path/to/file.png', storage='azure')
file_rackspace = client.store_from_url('http://bit.ly/1CzPVQp', storage='rackspace')
```

## Manipulating files

FilepickerFile objects can be created in three ways:

 - by uploading a file with using FilepickerClient
 - by initializing FilepickerFile with file handle
 - by initializing FilepickerFile with a Filepicker url

First method was shown above, the two other are also very easy and will create objects representing files that were already uploaded.

```python
from filepicker import FilepickerFile
file = FilepickerFile(handle='pGj2wWfBTMuXhWe2J3bL')
# or
file = FilepickerFile(url='https://www.filepicker.io/api/file/pGj2wWfBTMuXhWe2J3bL')
```

### File metadata

File objects initialized with file handle or url have only basic data available, like `file.url` or `file.handle`, but we can obtain detailed metadata with `update_metadata()` method:

```bash
>>> file = FilepickerFile('JMgn8KXMSbiG5bzHwEo4')
>>> file.url
'https://www.filepicker.io/api/file/JMgn8KXMSbXXXbzHwEo4'
>>> file.handle
'JMgn8KXMSbXXXbzHwEo4'
>>> file.metadata
{}
>>> print file.size
None
>>> file.update_metadata()
>>> file.metadata
{u'mimetype': u'image/png', u'uploaded': 1426695793592.9001, u'container': None, u'size': 66947, u'writeable': True, u'height': None, u'width': None, u'location': None, u'key': None, u'path': None, u'filename': 'image.png', u'md5': u'ec246f496a4be6ea32f72bc127e4f152'}
>>> file.size
66947
>>> file.mimetype
u'image/png'
```

As you can see, each metadata attribute can be easily accessed with `file.<attr_name>`.

### Download & delete

You can download and delete files represented by FilepickerFile objects using the `download()` and `delete()` methods, respectively.

```python
file.download('/home/user/files/downloaded_file.jpg')
file.delete()
```

To delete a file, your file object is required to have your API key set

```python
file.set_api_key('YOUR_API_KEY')
```

[TODO] key inheritance

### Overwriting files

You can upload your previously uploaded files with new ones

```python
file.overwrite(url='http://bit.ly/1CzPVQp')
# or with a local file
file.overwrite(filepath='/home/user/image.jpg')
```

### Image conversion

To take advantage of Filepicker's image post-processing, simply use the `convert()` method.
For example, here's all you need to do to add some blur and change width of your image:

```python
file.convert(w=400, filter='blur', blurAmount=4)
```

Files created like this are temporary and are not stored anywhere. You can only view and download them.
To store converted images, you need to provide one of our storing parameters, for example:

```python
file.convert(w=400, filter='blur', blurAmount=4, storeLocation='S3')
```

To learn more about our conversion and storing parameters, please check out [our docs](https://www.filepicker.com/documentation/file_processing/image_conversion/image)

## Security, policies and signatures

If you enable Security in our [Developer Portal](https://developers.filepicker.com/login/), uploading
and and accessing your files will require you create special policies. You can read more about them [here](https://www.filepicker.com/documentation/security/overview)

Filepicker library makes it really easy for you:

```python
client = FilepickerClient(api_key='YOUR_API_KEY',
                          app_secret='YOUR_APP_SECRET')
# or
# client.set_app_secret('YOUR_APP_SECRET')
client.add_policy(name='allow_storing',
                  policy={
                           'call': 'store',
                           'expiry': 1508141504
                          })
file = client.store_from_url('http://bit.ly/1CzPVQp', policy_name='allow_storing')

```

This also applies to FilepickerFile objects and their methods, like `download()`, `delete()`, `convert()` etc.

```python
file.add_policy('my_policy',
                {
                  'call': ['read', 'remove'],
                  'expiry': 1508141504
                 })
file.download('/home/user/file.jpg', policy_name='my_policy')
file.delete(policy_name='my_policy')
```

You can also generate file URLs with signature params:

```bash
>>> file = FilepickerFile(handle='pGj2wWfBTMuXhWe2J3bL')
>>> file.set_app_secret('APP_SECRET')
>>> file.add_policy('foo', {'call': 'read', 'expiry': 1508141504})
>>> file.get_signed_url(policy_name='foo')
'https://www.filepicker.io/api/file/pGj2wWfBTMuXhWe2J3bL?policy=eyJjYWxsIjogInJlYWQiLCAi&signature=6e493a379a2d00567162436b8ab11eb51ea259'
```

To learn more about our policies, please check out [our documentation](https://www.filepicker.com/documentation/file_processing/image_conversion/image)


## Contributing

Feel free to fork this repository, send pull requests or report bugs and issues on github.
