from app import app, login, admin, db
from flask import render_template, flash, redirect, url_for, request, session, \
    g, current_app, abort, jsonify
from flask_login import current_user, login_user, logout_user
from flask_login import login_required
from app.forms import *
from app.models import users_tbl, DbUser
import sys
import os
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from shutil import copyfile


@login.user_loader
def load_user(id):
    user = users_tbl.query.get(int(id))
    if user:
        return DbUser(user)
    else:
        return None

@app.route('/')
@app.route('/index')
def index():
    return render_template('main.html', title='home', page='home')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # checks if the user is authenticated , if they are it redirects the user
    # to the index page
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()

    # checks the form validation, if the user does not validate it returns
    # them to the login page and tells them invalid password or username
    if form.validate_on_submit():
        check_user = users_tbl.query.filter_by(email=form.email.data).first()
        user = DbUser(check_user)

        if check_user is None or not user.check_password(form.password.data):
            app.logger.warning('User fail to validate')
            flash('Invalid username or password')

            return redirect(url_for('login'))
        if not user.active:

            db.session.commit()

        # logs in the user sets them as active and directs them to the page
        # they tried to access if not it directs them to the index page
        if form.remember_me.data:
            login_user(user, remember=True)
        else:
            login_user(user, remember=False)

        next_page = request.args.get('next')

        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)

    return render_template('login.html', title='Sign In',
                           form=form, page='login')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """
    Logs user out
    """
    logout_user()
    flash('You have logged out')

    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = users_tbl(name=form.name.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/check_premium/<user>', methods=['GET','POST'])
def check_premium(user):
    """
    fetches the details of an user to fill in form data when updating that user
    """
    if user:
        cur_user = users_tbl.query.filter_by(id=user).first()

        UserObj = {}

        if cur_user.premium:
            UserObj["premium"] = True
        else:
            UserObj["premium"] = False

        return jsonify(UserObj)
    else:
        return "None"


@app.route('/login_user/<user>/<pw>', methods=['GET', 'POST'])
def login_app(user, pw):
    """
    fetches the details of an user to fill in form data when updating that user
    """
    if user:
        cur_user = users_tbl.query.filter_by(email=user).first()

        UserObj = {}

        user = DbUser(cur_user)
        if user.check_password(pw):
            UserObj["login"] = True
            if cur_user.premium:
                UserObj["premium"] = True
            else:
                UserObj["premium"] = False

        else:
            UserObj["login"] = False

        return jsonify(UserObj)
    else:
        return "None"

@app.route('/register_user/<name>/<user>/<pw>', methods=['GET', 'POST'])
def register_app(name, user, pw):
    """
    fetches the details of an user to fill in form data when updating that user
    """
    if user:
        user = users_tbl(name=name, email=user)
        user.set_password(pw)
        db.session.add(user)
        db.session.commit()
        cur_user = users_tbl.query.filter_by(email=user).first()

        UserObj = {}

        user = DbUser(cur_user)
        if user.check_password(pw):
            UserObj["login"] = True
            if cur_user.premium:
                UserObj["premium"] = True
            else:
                UserObj["premium"] = False

        else:
            UserObj["login"] = False

        return jsonify(UserObj)
    else:
        return "None"


@app.route("/update_details", methods=['Get', 'POST'])
def update_details():

    form = UpdateUser()
    if current_user.is_authenticated:
        form.user_name.data = current_user._user.name
        form.user_email.data = current_user._user.email
        if form.validate_on_submit():
            cur_user = users_tbl.query.filter_by(id=current_user._user.id).first()
            cur_user.name = form.user_name.data
            if form.user_new_email.data:
                cur_user.email = form.user_new_email.data
            if form.user_new_name.data:
                cur_user.name = form.user_new_name.data

            db.session.commit()
            flash("User details have been updated")
            return redirect(url_for("index"))

        return render_template('edit_details.html', form=form, page='Update details')
