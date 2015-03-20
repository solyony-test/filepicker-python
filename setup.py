import os
from setuptools import setup, find_packages

def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()

setup(
    name = 'filepicker',
    version = '0.2.0',
    license = 'ISC',
    description = 'Filepicker REST API Library',
    long_description = read('README.md'),
    url = 'https://github.com/filepicker/filepicker-python',
    author = 'filepicker.io',
    author_email = 'support@filepicker.io',
    packages = find_packages(),
    install_requires = [
        'requests',
    ],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP',
    ],
)
