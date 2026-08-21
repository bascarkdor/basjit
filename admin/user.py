import os
from flask import render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from extensions import db
from models.user import User
from . import admin_db
from flask_login import login_required

UPLOAD_FOLDER = 'static/uploads/avatars'


@admin_db.route('/users', methods=['GET'])
@login_required
def list_users():
    action = request.args.get('action')
    user_id = request.args.get('id', type=int)
    search_query = request.args.get('search', '').strip()
    role_filter = request.args.get('role', '').strip()

    edit_user = None
    if action == 'edit' and user_id:
        edit_user = User.query.get(user_id)

    query = User.query

    if search_query:
        query = query.filter(
            db.or_(
                User.name.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%')
            )
        )

    if role_filter:
        query = query.filter(User.role == role_filter)

    users = query.all()

    return render_template(
        'admin/page/user.html',
        users=users,
        edit_user=edit_user,
        search_query=search_query,
        role_filter=role_filter
    )


@admin_db.route('/users/add', methods=['POST'])
@login_required
def add_user():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')

    if not password:
        flash('Password is required when creating a new user.', 'danger')
        return redirect(url_for('admin.list_users', action='add'))

    hashed_password = generate_password_hash(password)

    avatar_file = request.files.get('avatar')
    avatar_path = f'https://ui-avatars.com/api/?name={name}'

    if avatar_file and avatar_file.filename != '':
        filename = secure_filename(avatar_file.filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        avatar_file.save(os.path.join(UPLOAD_FOLDER, filename))
        avatar_path = f'/{UPLOAD_FOLDER}/{filename}'

    new_user = User(
        name=name,
        email=email,
        password=hashed_password,
        role=role,
        avatar=avatar_path
    )
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('admin.list_users'))


@admin_db.route('/users/edit/<int:id>', methods=['POST'])
@login_required
def edit_user(id):
    user = User.query.get_or_404(id)
    user.name = request.form.get('name')
    user.email = request.form.get('email')
    user.role = request.form.get('role')

    # Hash and update password only if a new one was provided
    password = request.form.get('password')
    if password:
        user.password = generate_password_hash(password)

    avatar_file = request.files.get('avatar')
    if avatar_file and avatar_file.filename != '':
        filename = secure_filename(avatar_file.filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        avatar_file.save(os.path.join(UPLOAD_FOLDER, filename))
        user.avatar = f'/{UPLOAD_FOLDER}/{filename}'

    db.session.commit()
    return redirect(url_for('admin.list_users'))


@admin_db.route('/users/delete/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin.list_users'))