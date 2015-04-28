# -*- coding: utf-8 -*-
from flask import Flask, session, redirect, url_for, escape, request,render_template,flash,get_flashed_messages
app = Flask(__name__)

@app.route("/")
def index():
    if 'username' in session:
        return 'Logged in as %s' % escape(session['username'])
    return redirect(url_for('login'))

@app.route('/login',methods=['GET','POST'])
def login():
    app.logger.debug(get_flashed_messages())
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

app.secret_key = 'fd764a8237d7aae60a9135aa0ea6a7d2'

if __name__ == '__main__':
    app.debug = True
    app.run()
