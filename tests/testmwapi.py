# -*- coding: utf-8 -*-
# ============================================
#  __  __            _           _   
# |  \/  | ___   ___| |__   ___ | |_ 
# | |\/| |/ _ \ / _ \ '_ \ / _ \| __|
# | |  | | (_) |  __/ |_) | (_) | |_ 
# |_|  |_|\___/ \___|_.__/ \___/ \__|
# 
# --------------------------------------------
# @Author: grzhan
# @Date:   2015-04-28
# @Email:  i@grr.moe
# @Description: 针对mwapi.py的单元测试
# 

from unittest import main,TestCase
from ..mwapi import (login as mwlogin, get_edit_token as mwtoken, get_pid as mwpid,
	get_content as mwcontent,edit as mwedit)

class TestMediaWikiAPI(TestCase):
	def setUp(self):
		self.host = 'http://192.168.10.10/mediawiki/api.php'
		self.username = 'grzhan'
		self.password = '123456'
	
	def testlogin(self):
		ret = mwlogin(self.host,self.username,self.password)
		if not ret['success']:
			print 
			print ret['errtitle']
			print ret['errmsg']
		self.assert_(ret['success'])

	def testgetpid(self):
		# title = '舰队Collection:比睿'
		title = 'Talk:提问求助区'
		ret = mwpid(self.host,title)
		if not ret['success']:
			print 
			print ret['errtitle']
			print ret['errmsg']
		# else:
			print ret['pageid']
		self.assert_(ret['success'])

	def testgetcontent(self):
		# pageid = 7		# Title: 舰队Collection:比睿
		pageid = 9          # Title: Talk:提问求助区
		ret = mwcontent(self.host, pageid)
		if not ret['success']:
			print 
			print ret['errtitle']
			print ret['errmsg']
		self.assert_(ret['success'])

	def testedit(self):
		signin_cookie = mwlogin(self.host,self.username,self.password)['cookie']
		ret = mwedit(self.host,'test','test',signin_cookie, title='舰队Collection:长门')
		if not ret['success']:
			print 
			print ret['errtitle']
			print ret['errmsg']
		self.assert_(ret['success'])

if __name__ == '__main__':
	main()