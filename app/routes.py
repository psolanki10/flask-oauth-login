from flask import render_template, flash, redirect, url_for, request
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, UpdatePasswordForm
from app.models import User
from flask_login import current_user, login_user, logout_user, login_required
from flask_dance.contrib.google import google


@app.route('/index')
def index():
    return render_template('index.html', title='Home')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user', identifier=current_user.username))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/glogin')
def glogin():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v1/userinfo")
    assert resp.ok, resp.text
    resp = resp.json()

    user = User.query.filter_by(email=resp['email']).first()
    if user is None:
        user = User(name=resp["name"], email=resp["email"],
                    username=resp["given_name"].lower() + '_' + resp["family_name"].lower())
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('You have successfully signed in through your Google ID!')
        flash('Your username is autogenerated. You can change it later.')
        return redirect(url_for('user', identifier=current_user.username))

    login_user(user)
    flash('You have successfully signed in through your Google ID!')
    return redirect(url_for('user', identifier=current_user.username))


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user', identifier=current_user.username))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('user', identifier=current_user.username))


        # Restricted access page, grant access only after logging in
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')  #todo - error page

        return redirect(next_page)

    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


# TODO - sort out id stuff, make it work
@app.route('/user/<identifier>')
@login_required
def user(identifier):
    # Check if identifire is id or username
    if isinstance(identifier, int):
        if identifier != current_user.id:
            return redirect(url_for('index'))
        user = User.query.filter_by(id=current_user.id).first_or_404()
    else:
        #todo (done) - show profile page only if passed username and current_user are same
        if identifier != current_user.username:
            return redirect(url_for('index')) #todo - error page or restricted pageds
        user = User.query.filter_by(username=current_user.username).first_or_404()

    return render_template('user.html', user=user)


@app.route('/update_password', methods=['GET', 'POST'])
@login_required
def update_password():
    form = UpdatePasswordForm()
    if form.validate_on_submit():
        if hasattr(current_user, 'password'):
            if current_user.check_password(form.password.data):
                flash("New password cannot be same as previous password.")
                return redirect(url_for('update_password'))

        current_user.set_password(form.password.data)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user', identifier=current_user.username))

    # elif request.method == 'GET':
    #     form.username.data = current_user.username
    #     form.email.data = current_user.email
    #     if hasattr(current_user, 'password'):
    #         form.password.data = current_user.password

    return render_template('update_password.html', title='Set/Update Password', form=form)
