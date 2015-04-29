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
# @Description: Task:Talk Backup 讨论板备份任务
# 

from moebot.Moebot import celery
from moebot import mwapi
import os
import datetime
import pytz
import re

def text_process(content):	
	# I. 去掉{{模板:提问求助区页顶}}
	pattern = re.compile(r'\{\{\s*模板\s*:\s*提问求助区页顶\s*\}\}')
	content = pattern.sub('', content)

	# II. 去掉{{无人继续恢复|...}}\{{问题已解决|...}}
	pattern = re.compile(r'\{\{\s*问题已解决\s*\|\s*内容\=(.*?)\}\}', re.DOTALL)
	content = pattern.sub(r'\1', content)
	pattern = re.compile(r'\{\{\s*无人继续回复\s*\|\s*内容\=(.*?)\}\}', re.DOTALL)
	content = pattern.sub(r'\1', content)

	# 设定日期与二级标题的匹配模式
	date_pattern = re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日\s*?\(.*?\)\s*?(\d{2}):(\d{2})\s*?\(CST\)')
	section_pattern = re.compile(r'^={2}[^=]*?={2}\s*?$', re.MULTILINE)

	# 查找所有二级标题
	sections = section_pattern.findall(content)

	# 提取所有二级标题下的内容
	section_contents= section_pattern.split(content)

	# 存档没有在三天内回复的主题
	tz = pytz.timezone('Asia/Shanghai')
	now = datetime.datetime.now(tz)
	three_days_ago = now - datetime.timedelta(days=3)
	newcontent = section_contents[0]
	for i,section in enumerate(sections):
		section_content = section_contents[i+1]
		fpass = False
		for date in date_pattern.findall(section_content):
			reply_time = datetime.datetime(int(date[0]), int(date[1]), 
				int(date[2]),int(date[3]),int(date[4]),tzinfo=tz)
			if reply_time > three_days_ago:
				fpass = True
				break
		if not fpass:
			newcontent += section
			newcontent += section_content
		else:
			prompt('【{sec}】存在三天内的回复，故不存档'.format(sec=section))
			hrprint('-')
	return newcontent


@celery.task(bind=True)
def talk_backup(self):
	"""
	Task:Talk Backup 讨论板备份
	针对每月提问/讨论区进行备份，备份时进行的文本处理参见text_process函数
	"""
	username = 'grzhan'
	password = '123456'
	reason   = 'Talk Backup 测试'
	host = 'http://192.168.10.10/mediawiki/api.php'
	title = 'Talk:提问求助区'

	# Get signin session
	ret = mwapi.login(host, username, password)
	if ret['success']:
		signin_cookies = ret['cookie']

	# Get page id
	ret = mwapi.get_pid(host, title)
	if ret['success']:
		pid = ret['pageid']
	else:
		return 'Failed'

	# Get page content
	ret = mwapi.get_content(host,pid)
	if ret['success']:
		content = ret['content']
		return content
	else:
		return 'Failed'

	# Get Processed content
	ncontent = text_process(content)

	# Get Current Month
	tz = pytz.timezone('Asia/Shanghai')
	month = datetime.datetime.now(tz).month
	
	# ntitle = 'Talk:提问求助区/存档/2015年%.2d月' % (month)
	ntitle = 'User:Grzhan/SandBox'
	reason = reason.replace('@title', ntitle)

	# 备份处理后的文本
	ret = mwapi.edit(host, ncontent, reason, signin_cookies,title=ntitle)
	if ret['success']:
		return 'Success'
	else:
		return ret


