from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from . import admin_db  # Using admin_db here


@admin_db.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and (user.check_password(password) or user.password == password):
            login_user(user)
            return redirect(url_for('admin.dashboard'))

        flash('Invalid email or password', 'error')

    return render_template('admin/Auth/login.html')


@admin_db.route('/logout')
@login_required
def logout():
    logout_user()      # 1. Logs out user from Flask-Login
    session.clear()    # 2. Clears all session keys
    return redirect(url_for('admin.login'))  # 3. Redirects to admin login