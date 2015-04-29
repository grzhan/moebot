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
# @Date:   2015-04-29
# @Email:  i@grr.moe
# @Description: 针对Task:TalkBackup的单元测试
# 

from moebot.tasks.talkbackup import talk_backup,text_process
from unittest import main,TestCase

class TestTaskTalkBackup(TestCase):
	def setUp(self):
		self.config = dict()
		self.config['username'] = 'grzhan'
		self.config['password'] = '123456'
		self.config['reason']   = 'Talk Backup 测试'
		self.config['host'] = 'http://192.168.10.10/mediawiki/api.php'
		self.config['title'] = 'Talk:提问求助区'
		self.config['target'] = 'User:Grzhan/SandBox'

		pass
	def testtask(self):
		result = talk_backup.delay(self.config)
		ret = result.get()
		print ret
		self.assert_(ret['success'])


	def testtextprocess(self):
		self.assert_(True)		

if __name__ == '__main__':
	main()

