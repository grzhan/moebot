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
# @Description: 一个简单调用Mediawiki API的中间层，
# 				统一返回值的规范并处理网络、目标站点崩溃等异常
# 


DEBUG = True
if not DEBUG:
	from moebot import app

from requests import get,post,ConnectionError,HTTPError,Timeout,TooManyRedirects


def banner():
	ascii_text = '''
 __  __            _           _   
|  \/  | ___   ___| |__   ___ | |_ 
| |\/| |/ _ \ / _ \ '_ \ / _ \| __|
| |  | | (_) |  __/ |_) | (_) | |_ 
|_|  |_|\___/ \___|_.__/ \___/ \__|
'''
	return ascii_text


def MediaWikiAPI(func):
	"""
	MediaWikiAPI 控制API请求异常的装饰器
	根据requests库定义的异常来控制请求返回的意外情况
	"""
	def wrapper(*args,**kwargs):
		host = args[0]
		try:
			result = func(*args,**kwargs)
			return result
		except ConnectionError:
			err_title = '连接错误'
			err_message = '[{name}] 连接错误，网络状况异常'.format(name=func.__name__,host=host)
		except HTTPError as e:
			err_title = 'HTTP响应错误'
			err_message = '[{name}] 目标服务器"{host}" HTTP响应错误({detail})'.format(name=func.__name__,
				host=host,detail=e.message)
		except Timeout:
			err_title = '请求超时'
			err_message = '[{name}] 目标服务器"{host}" 请求超时'.format(name=func.__name__,host=host)
		except TooManyRedirects:
			err_title = '过多重定向'
			err_message = '[{name}] 目标服务器"{host}" 过多重定向'.format(name=func.__name__,host=host)
		except ValueError as e:
			if e.message.find('JSON') >= 0:
				err_title = 'API JSON返回值异常'
				err_message = '[{name}] 目标服务器"{host}" API JSON返回值异常'.format(name=func.__name__,host=host)
			else:
				err_title = 'Value Error'
				err_message = e.message
		if not DEBUG:
			app.logger.error(err_message)		
		return {'success': False, 'errtitle': err_title, 'errmsg': err_message}
	return wrapper
	
		
@MediaWikiAPI
def get_edit_token(host,cookie):
	rep = get(host + '?action=query&meta=tokens&format=json',cookies=cookie)
	return {'success': True, 'token': rep.json()['query']['tokens']['csrftoken']}

@MediaWikiAPI
def login(host,username,password):
	rdata = {'action':'login','format':'json'}
	rdata['lgname'] = username
	rdata['lgpassword'] = password
	# 第一次登陆验证
	rep = post(host,rdata)
	cookie = rep.cookies.get_dict()
	if cookie == {}:
		return {'success': False, 'errtitle': '初步登陆验证失败',
		'errmsg':'登陆响应Cookie为空，请检查Mediawiki的用户名密码是否正确'}
	rdata['lgtoken'] = response.json()['login']['token']
	# 第二次登陆验证
	rep = post(host,rdata,cookies=cookie)
	signin_cookie = rep.cookies.get_dict()
	if signin_cookie == {}:
		return {'success': False, 'errtitle': '登陆验证失败',
		'errmsg':'二步登陆响应Cookie为空，请联系开发者检查有关程序'}	
	signin_cookie.update(cookie)
	return {'success': True, 'json': rep.json(), 'cookie': signin_cookie}


