from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from extensions import db, limiter
from . import user_db

def is_safe_redirect(url):
    return bool(url and url.startswith('/') and not url.startswith('//'))

@user_db.route('/register', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
def register():
    next_url = request.form.get('next') or request.args.get('next')

    if current_user.is_authenticated:
        if is_safe_redirect(next_url):
            return redirect(next_url)
        return redirect(url_for('.home'))

    if request.method == 'POST':
        fullname = (request.form.get('fullname') or request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        confirm_password = request.form.get('confirm_password') or ''

        if not fullname or not email or not password:
            flash('Please fill in all required fields.', 'danger')
            return render_template('user/page/register.html', next=next_url)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('user/page/register.html', next=next_url)

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already registered.', 'danger')
            return render_template('user/page/register.html', next=next_url)

        new_user = User(
            name=fullname,
            email=email,
            avatar=f'https://ui-avatars.com/api/?name={fullname}',
            role='Customer'
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash('Registration successful! Welcome.', 'success')

        if is_safe_redirect(next_url):
            return redirect(next_url)
        return redirect(url_for('.home'))

    return render_template('user/page/register.html', next=next_url)

@user_db.route('/login', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
def login():
    next_url = request.form.get('next') or request.args.get('next')

    if current_user.is_authenticated:
        if is_safe_redirect(next_url):
            return redirect(next_url)
        return redirect(url_for('.home'))

    if request.method == 'POST':
        identifier = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        remember = True if request.form.get('remember') else False

        user = User.query.filter(
            (User.email == identifier.lower()) | (User.name == identifier)
        ).first()

        if user and (user.check_password(password) or user.password == password):
            login_user(user, remember=remember)
            flash('Logged in successfully!', 'success')
            if is_safe_redirect(next_url):
                return redirect(next_url)
            return redirect(url_for('.home'))

        flash('Invalid username/email or password.', 'danger')

    return render_template('user/page/login.html', next=next_url)

@user_db.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('.login'))
