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
# @Description: Moebot是方便Mediawiki编辑者的自动脚本机器人
from __future__ import absolute_import

from flask import (Flask, session, redirect, url_for, escape, 
    request,render_template,flash,get_flashed_messages,g)
from flask.ext.script import Manager
from celery import Celery
app = Flask(__name__)

app.secret_key = 'fd764a8237d7aae60a9135aa0ea6a7d2'

@app.route("/")
def index():
    if 'username' in session:
        conf = g.redis.get('task.talkbackup.conf')
        if not conf is None:
            config = json.loads(conf)
        return render_template('form.html',conf=config)        
    return redirect(url_for('login'))

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'test' and password == 'sometimes':
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash(u'用户名或密码不匹配，请重新输入')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


from redis import Redis

@app.before_request
def before_request():
    g.redis = Redis(host='localhost',port='6379')


@app.route('/task/start',methods=['GET','POST'])
def task_start():
    if not 'username' in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        g.redis.set('task.talkbackup.conf', json.dumps(request.form))
    conf = g.redis.get('task.talkbackup.conf')
    if not conf is None:
        config = json.loads(conf)
        print config
        task = talk_backup.delay(config)
        g.redis.set('task.talkbackup.id', task.id)
        return redirect(url_for('task_status'))
    else:
        return '获取配置内容失败'

@app.route('/task/status')
def task_status():
    tid = g.redis.get('task.talkbackup.id')
    if not tid is None:
        task = talk_backup.AsyncResult(tid)
        if task.state == 'PROGRESS':
            return task.info.get('status')
        elif task.state == 'SUCCESS':
            if task.info.get('success'):
                return '任务执行成功！'
            else:
                return task.info.get('errmsg')
        else:
            return str(task.info)

@app.route('/task/config')
def task_config():
    return g.redis.get('task.talkbackup.conf')

@app.route('/task/config/init')
def task_init():
    config = dict()
    config['username'] = 'grtest'
    config['password'] = '123456'
    config['reason']   = u'Talk Backup 测试'
    config['host'] = 'http://zh.moegirl.org/api.php'
    config['title'] = u'Talk:提问求助区'
    config['target'] = 'User:Grtest/SandBox'
    if g.redis.set('task.talkbackup.conf',json.dumps(config)):
        return '配置成功'
    else:
        return '配置失败'


def make_celery(app):
    celery = Celery('moebot', broker=app.config['CELERY_BROKER_URL'], 
        backend=app.config['CELERY_RESULT_BACKEND'],
        # include=['moebot.tasks.talkbackup']
    )
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(app)

# Include : talk_back_up
import mwapi
import datetime
import pytz
import re
import json

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
    return newcontent


@celery.task(bind=True)
def talk_backup(self,config):
    """
    Task:Talk Backup 讨论板备份
    针对每月提问/讨论区进行备份，备份时进行的文本处理参见text_process函数
    """
    username = config['username'].encode('utf-8')
    password = config['password']
    reason   = config['reason'].encode('utf-8')
    host     = config['host']
    title    = config['title'].encode('utf-8')
    target   = config['target'].encode('utf-8')

    # Get signin session
    self.update_state(state='PROGRESS',meta={'current':1, 'total': 5, 
        'status': '【{user}】正在登陆'.format(user=username)})
    ret = mwapi.login(host, username, password)
    if ret['success']:
        signin_cookies = ret['cookie']
    else:
        return {'success': False, 'errmsg': ret['errmsg'], 'errtitle': ret['errtitle']}

    # Get page id
    self.update_state(state='PROGRESS',meta={'current':2, 'total': 5, 
        'status': '获取【{title}】页面ID'.format(title=title)})       
    ret = mwapi.get_pid(host, title)
    if ret['success']:
        pid = ret['pageid']
    else:
        return {'success': False, 'errmsg': ret['errmsg'], 'errtitle': ret['errtitle']}

    # Get page content
    self.update_state(state='PROGRESS',meta={'current':3, 'total': 5, 
        'status': '页面ID为{pid}，获取【{title}】页面内容'.format(title=title,pid=pid)})        
    ret = mwapi.get_content(host,pid)
    if ret['success']:
        content = ret['content']
    else:
        return {'success': False, 'errmsg': ret['errmsg'], 'errtitle': ret['errtitle']}

    # Get Processed content
    ncontent = text_process(content)
    
    # Get Current Month
    tz = pytz.timezone('Asia/Shanghai')
    month = datetime.datetime.now(tz).month
    
    # ntitle = 'Talk:提问求助区/存档/2015年%.2d月' % (month)
    ntitle = target
    reason = reason.replace('@title', ntitle)

    # 备份处理后的文本
    self.update_state(state='PROGRESS',meta={'current':4, 'total': 5, 
        'status': '文本处理完毕，正在备份到【{title}】'.format(title=ntitle)})    
    ret = mwapi.edit(host, ncontent, reason, signin_cookies,title=ntitle)
    if ret['success']:
        return {'success': True, 'status': '备份成功！', 'current':5, 'total': 5}
    else:
        return {'success': False, 'errmsg': ret['errmsg'], 'errtitle': ret['errtitle']}


if __name__ == '__main__':
    app.debug = True
    manager = Manager(app)
    manager.run()
