Filepicker Python Library
===================

This module provides an easy way to use [Filepicker's REST API](https://www.filepicker.com/documentation/file_ingestion/rest_api/retrieving) in your Python projects.

# Installation

Install ``filepicker`` with pip:

    $ pip install filepicker

or directly from GitHub [TODO]

    $ pip install git+https://github.com/filepicker/filepicker-python.git

It will also install `requests` and `httmock` library.

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


## Contributing
Feel free to fork, send pull requests or report bugs and issues on github.
