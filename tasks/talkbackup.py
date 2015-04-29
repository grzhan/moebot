from ..moebot import celery,app
from .. import mwapi
import os
import datetime
import pytz

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
	针对每月提问/讨论区进行备份，备份的要求如下：
	...
	"""
	username = 'grzhan'
	password = '123456'
	reason   = 'Talk Backup 测试'
	sign_cookies = mwapi.login(host, username, password)
	title = 'Talk:提问求助区'

	# Get page id
	pid = mwapi.get_pid(host, title)

	# Get page content
	content = get_content(host,pid)

	# Get Processed content
	ncontent = text_process(content)

	# Get Current Month
	tz = pytz.timezone('Asia/Shanghai')
	month = datetime.datetime.now(tz).month
	# ntitle = 'Talk:提问求助区/存档/2015年%.2d月' % (month)
	ntitle = 'User:AnnAngela/SandBox'

	reason = reason.replace('@title', ntitle)
	print ncontent
	rep = edit(host, ncontent, reason, signin_cookies,title=ntitle)
	if not rep is None:
		prompt('存档成功！')

