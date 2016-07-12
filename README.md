# moebot

A simple mediawiki API wrapper, implemented by python. 

alpha version..

## Install

	python setup.py install

## Usage

	from moebot import MwApi
	mw = MwApi('http://zh.kcwiki.moe/api.php')
	mw.login(username, password)

### Upload

	mw.upload(filepath[, filename])