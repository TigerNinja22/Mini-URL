# -*- coding: utf-8 -*-
# Copyright (c) 2022 Arjun Ladha

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Mini-URL
~~~~~~~~~
A free URL shortener for everyone

:copyright: 2021-present Arjun Ladha
:license: MIT
"""

import os
import bcrypt

from dotenv import load_dotenv

from flask import Flask, redirect, render_template, request, url_for
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, EmailField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError

from flask_bcrypt import Bcrypt

from utility import *

app = Flask("Mini URL")
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
load_dotenv()

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.secret_key = os.getenv("FLASK_SECRET_KEY")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(36), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(254), nullable=False)

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(),
                                       Length(min=4, max=36)],
                           render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(),
                                       Length(min=8, max=16)],
                           render_kw={"placeholder": "Password"})
    email = EmailField(validators=[InputRequired(),
                                       Length(min=8, max=16)],
                           render_kw={"placeholder": "Email"})
    
    submit = SubmitField("Register")
    
    def validate_username(self, username):
        if existing_user_username := User.query.filter_by(username=username.data).first():
            return ValidationError("That username is already exists. Please choose a different one.")

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(),
                                       Length(min=4, max=36)],
                           render_kw={"placeholder": "Username"})
    
    password = PasswordField(validators=[InputRequired(),
                                       Length(min=8, max=16)],
                           render_kw={"placeholder": "Password"})
    
    submit = SubmitField("Login")


def check_username(username):
    return not (existing_user_username := User.query.filter_by(username=username).first())

def check_email(email):
    return not (existing_user_email := User.query.filter_by(email=email).first())


@app.route('/')
@app.route('/home')
@app.route('/index')
def home():
    return render_template('base.html')

@app.route('/url', methods=['POST', 'GET'])
def url():
    if request.method == 'POST':
        return request.form['url']
    else:
        return render_template('url_page.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        if user := User.query.filter_by(username=form.username.data).first() or User.query.filter_by(email=form.username.data).first():
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                return render_template('userauth/login/login_wrong_info.html', form=form)

    return render_template('userauth/login/login.html', form=form)

@app.route('/dasboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('user/dashboard.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
    
@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        if not check_username(form.username.data):
            return render_template('userauth/register/register_username_exists.html', form=form)
        if not check_email(form.email.data):
            return render_template('userauth/register/register_email_exists.html', form=form)
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password, email=form.email.data)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('userauth/register/register.html', form=form)

@app.route('/<short_url>')
def redirection(short_url):
    long_url = get_long_url(short_url)
    if long_url is False:
        return render_template('error/urlnotfound.html')
    else:
        return redirect(str(long_url))


# ROUTES FOR TEST PURPOSES
@app.route('/allurls')
def all_urls():
    # grab all urls from the database and display them (FOR TEST PURPOSES)
    docs = get_all_docs()
    return render_template('dev/all_urls.html', docs=docs)

@app.route('/alldocs')
def all_docs():
    # grab all urls from the database and display them (FOR TEST PURPOSES)
    docs = get_all_docs()
    return render_template('dev/all_docs.html', docs=docs)

if __name__ == '__main__':
    app.run(debug=True)
