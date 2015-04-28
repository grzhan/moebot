#-*- coding: utf-8 -*-
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
from ..mwapi import login as mwlogin, get_edit_token as mwtoken

class TestMediaWikiAPI(TestCase):
	def setUp(self):
		self.host = 'http://192.168.10.10/mediawiki/api.php'
		self.username = 'grzhan'
		self.password = '123456'
	def testlogin(self):
		ret = mwlogin(self.host,self.username,self.password)
		print ret['json']
		self.assert_(ret['success'])

if __name__ == '__main__':
	main()