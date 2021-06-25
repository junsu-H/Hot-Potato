# vim hot/routes.py

from flask import render_template, request, redirect, url_for, session
import re
from hot import app
from hot.models import User, News, Private, Public
import bcrypt

app.secret_key = 'your secret key'

news = [] 
# keyword, summary, url
@app.route('/test')
def test():
    temp = News.news_all_load()
    accounts_id = int(User.get_id(session['username'])['id'])
    global news

    for i in range(len(temp)):
        news.append(temp[i].values())
    return render_template('test.html', news=news)

@app.route('/private')
def private():
    accounts_id = int(User.get_id(session['username'])['id'])
    temp = Private.private_ranking(accounts_id)
    private = []
    for i in range(len(temp)):
        private.append(temp[i].values())

    return render_template('private.html', private=private)

@app.route('/public')
def public():
    temp = Public.public_ranking()
    public = []
    for i in range(len(temp)):
        public.append(temp[i].values())
    return render_template('public.html', public=public)
   
   
@app.route('/rating', methods=['GET', 'POST'])
def rating():
    accounts_id = int(User.get_id(session['username'])['id'])
    news_id = int(request.form['newsId'])
    rate = int(request.form['rate'])
    try:
        News.insert_rating(accounts_id, news_id, rate)
        select_rate = News.select_rating(accounts_id, news_id)
    
    except:
        News.update_rating(accounts_id, news_id, rate)
        select_rate = News.select_rating(accounts_id, news_id)
    return redirect('/test')
    
@app.route('/rate/<id>')
def select_rate(id):
    try:
        accounts_id = int(User.get_id(session['username'])['id'])
        select_rate = News.select_rating(accounts_id, id)
        return "rate: " +  str(select_rate[0]['rate'])
    except:
        return "rate: 0"

@app.route('/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = 'Creating User Page'
    # If already loggedin, redirect to home
    if 'loggedin' in session:
        return redirect(url_for('home'))
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        username_already_exist = User.check_username_exist(username)
        if username_already_exist:
            msg = 'That username is already exist'
        else:
            User.account_add(username, password)
            msg = 'Create User Success!'
            return redirect(url_for('login'))
    return render_template('register.html', msg=msg)

@app.route('/',  methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    try:
        msg = ''
        if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
            username = request.form['username']
            password = request.form['password']

            account, check_password  = User.login_check(username, password)
            if check_password:
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']

                return redirect(url_for('home'))
            else:
                msg = 'Incorrect username/password!'
    
        if 'loggedin' in session:
            return redirect(url_for('home'))

        # Show the login form with message (if any)
        return render_template('login.html', msg=msg)
    except:
        return render_template('index.html', msg=msg)

@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))

@app.route('/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        account = User.get_information([session['id']])
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
