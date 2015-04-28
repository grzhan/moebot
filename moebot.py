# -*- coding: utf-8 -*-
from flask import Flask, session, redirect, url_for, escape, request,render_template,flash,get_flashed_messages
from flask.ext.script import Manager
from celery import Celery
app = Flask(__name__)

@app.route("/")
def index():
    if 'username' in session:
        return 'Logged in as %s' % escape(session['username'])
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

@app.route('/celery/test')
def celery_test():
    result = add.delay(1,2)
    app.logger.debug(result.state)
    return '任务发布成功'


app.secret_key = 'fd764a8237d7aae60a9135aa0ea6a7d2'

def make_celery(app):
    celery = Celery('moebot', broker=app.config['CELERY_BROKER_URL'], 
        backend=app.config['CELERY_RESULT_BACKEND'])
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

@celery.task
def add(a,b):
    return a+b


if __name__ == '__main__':
    app.debug = True
    manager = Manager(app)
    manager.run()
