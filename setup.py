from setuptools import setup, find_packages
from moebot import VERSION, __author__, __email__

setup(
    name='moebot',
    version=VERSION,
    author_email=__email__,
    author=__author__,
    packages=find_packages(),
    description='A simple mediawiki API wrapper',
    url='https://github.com/grzhan/moebot',
    download_url='https://github.com/grzhan/moebot/tarball/' + VERSION,
    keywords=['mediawiki', 'wrapper', 'api'],
    license='MIT'
)
