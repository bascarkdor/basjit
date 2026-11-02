from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user
from extensions import db
from . import user_db

@user_db.route('/settings')
def settings():
    return render_template('user/page/setting.html')

@user_db.route('/settings/update', methods=['POST'])
def update_settings():
    username = request.form.get('username')
    email = request.form.get('email')

    if current_user.is_authenticated:
        if username:
            current_user.name = username
        if email:
            current_user.email = email
        db.session.commit()
        flash('Account settings updated successfully!', 'success')
    else:
        flash('Settings saved successfully!', 'success')

    return redirect(url_for('.settings'))