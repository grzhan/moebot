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

from __future__ import absolute_import

from moebot.tasks.talkbackup import talk_backup,text_process
from unittest import main,TestCase

class TestTaskTalkBackup(TestCase):
	def setUp(self):
		pass
	def testtask(self):
		result = talk_backup.delay()
		ret = result.get()
		print ret
		self.assert_(ret == 'Success')


	def testtextprocess(self):
		self.assert_(True)		

if __name__ == '__main__':
	main()

