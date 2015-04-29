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
	from Moebot import app

from requests import get,post,ConnectionError,HTTPError,Timeout,TooManyRedirects

class MWAPIException(Exception):
	"""
	MWAPIException MWAPI函数中异常
	"""
	pass


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
				err_title = '值错误'
				err_message = '[{name}] 存在ValueError：{msg}'.format(name=func.__name__,msg=e.message)
		except KeyError as e:
			err_title = '键错误'
			err_title = '[{name}] 存在KeyError，错误键为{key}'.format(name=func.__name__,key=e.message)

		except MWAPIException as e:
			err_title = 'Mediawiki API 异常'
			err_message = e.message

		global DEBUG
		if not DEBUG:
			app.logger.error(err_message)		
		return {'success': False, 'errtitle': err_title, 'errmsg': err_message}
	return wrapper
	
@MediaWikiAPI
def login(host,username,password):
	rdata = {'action':'login','format':'json'}
	rdata['lgname'] = username
	rdata['lgpassword'] = password
	# 第一次登陆验证
	rep = post(host,rdata)
	cookie = rep.cookies.get_dict()
	result = rep.json()['login']['result']
	if result == 'NoName':
		raise MWAPIException('Mediawiki用户未填写')
	if cookie == {}:
		raise MWAPIException('登陆响应Cookie为空，请检查Mediawiki的用户名密码是否正确')
	rdata['lgtoken'] = rep.json()['login']['token']
	
	# 第二次登陆验证
	rep = post(host,rdata,cookies=cookie)
	result = rep.json()['login']['result']
	if result == 'Success':	
		signin_cookie = rep.cookies.get_dict()
		if signin_cookie == {}:
			raise MWAPIException('二步登陆响应Cookie为空，请联系开发者检查有关程序')
		signin_cookie.update(cookie)
		return {'success': True, 'json': rep.json(), 'cookie': signin_cookie}
	elif result == 'WrongPass':
		raise MWAPIException('Mediawiki登陆密码错误')
	elif result == 'EmptyPass':
		raise MWAPIException('Mediawiki密码未填写')
	elif result == 'NotExists':
		raise MWAPIException('Mediawiki该用户不存在')
	else:
		raise MWAPIException(u'登陆异常：' + result)

		
@MediaWikiAPI
def get_edit_token(host,cookie):
	rep = get(host + '?action=query&meta=tokens&format=json',cookies=cookie)
	return {'success': True, 'token': rep.json()['query']['tokens']['csrftoken']}

@MediaWikiAPI
def get_pid(host,title):
	rdata = {'action':'query','format':'json'}
	rdata['titles'] = title
	rep = post(host,rdata)
	pid = rep.json()['query']['pages'].keys()[0]
	if int(pid) < 0:
		raise MWAPIException('请求页面【{title}】不存在'.format(title=title))
	return {'success': True, 'pageid': pid}

@MediaWikiAPI
def get_content(host,pageid):
	rdata = {'action':'query','prop':'revisions','format':'json'}
	rdata['rvprop'] = 'timestamp|user|comment|content'
	rdata['pageids'] = pageid
	rep = post(host,rdata)
	if rep.json()['query']['pages'][str(pageid)].has_key('missing'):
		raise MWAPIException('Mediawiki请求页面内容({pid})不存在'.format(pid=pageid))
	content = rep.json()['query']['pages'][str(pageid)]['revisions'][0]['*'].encode('utf-8')
	return {'success': True, 'content': content}

@MediaWikiAPI
def edit(host,content,reason, cookie,pageid=None, title = None):
	rdata = {'action':'edit','format':'json'}
	if pageid:
		rdata['pageid'] = pageid
	elif title:
		rdata['title'] = title
	rdata['text'] = content
	rdata['bot'] = 1
	rdata['summary'] = reason
	token_result = get_edit_token(host, cookie)
	if token_result['success']:
		rdata['token'] = token_result['token']
	else:
		raise MWAPIException('编辑token获取失败')
	headers = {'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}
	rep = post(host, data=rdata, headers=headers, cookies=cookie)
	rep_json = rep.json()
	if rep_json.has_key('edit') and rep_json['edit'].has_key('result') \
	and rep_json['edit']['result'] == 'Success':
		return {'success': True, 'json': rep_json}
	# TODO 对于编辑结果异常的细化处理
	elif rep_json.has_key('error'):
		raise MWAPIException('编辑失败，出错码【{code}】:{info}'.format(code=rep_json['error']['code'],
			info=rep_json['error']['info']))
	else:
		raise MWAPIException('编辑失败，未知错误：{json}'.format(json=rep_json))




