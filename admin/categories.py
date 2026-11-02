import os
import uuid
from flask import render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask_login import login_required
from extensions import db, limiter
from models.category import Category
from . import admin_db

UPLOAD_FOLDER = 'static/uploads/categories'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_db.route('/categories', methods=['GET'])
@login_required
@limiter.exempt
def categories():
    action = request.args.get('action')
    category_id = request.args.get('id', type=int)
    search_query = request.args.get('search', '').strip()

    edit_category = None
    if action == 'edit' and category_id:
        edit_category = Category.query.get(category_id)

    query = Category.query
    if search_query:
        query = query.filter(Category.name.ilike(f'%{search_query}%'))

    all_categories = query.order_by(Category.id.desc()).all()

    # Calculate summary metrics
    total_categories = len(all_categories) if not search_query else Category.query.count()
    total_products_linked = sum(c.product_count for c in all_categories)

    return render_template(
        'admin/page/Category.html',
        categories=all_categories,
        edit_category=edit_category,
        action=action,
        search_query=search_query,
        total_categories=total_categories,
        total_products_linked=total_products_linked
    )

@admin_db.route('/categories/add', methods=['POST'])
@login_required
@limiter.exempt
def add_category():
    name = request.form.get('name', '').strip()
    img_url = request.form.get('img_url', '').strip()
    img_file = request.files.get('img_file')

    if not name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('admin.categories', action='add'))

    existing = Category.query.filter_by(name=name).first()
    if existing:
        flash(f'A category named "{name}" already exists.', 'warning')
        return redirect(url_for('admin.categories', action='add'))

    final_img_path = img_url if img_url else None

    # Handle image file upload
    if img_file and img_file.filename:
        if allowed_file(img_file.filename):
            ext = img_file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"cat_{uuid.uuid4().hex[:10]}.{ext}"
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            img_file.save(save_path)
            final_img_path = f"/{UPLOAD_FOLDER}/{unique_filename}"
        else:
            flash('Invalid image file format. Allowed: PNG, JPG, JPEG, GIF, WEBP, SVG.', 'warning')

    new_cat = Category(name=name, img=final_img_path)
    db.session.add(new_cat)
    db.session.commit()
    flash(f'Category "{name}" created successfully.', 'success')
    return redirect(url_for('admin.categories'))

@admin_db.route('/categories/edit/<int:id>', methods=['POST'])
@login_required
@limiter.exempt
def edit_category(id):
    category = Category.query.get_or_404(id)
    name = request.form.get('name', '').strip()
    img_url = request.form.get('img_url', '').strip()
    img_file = request.files.get('img_file')

    if not name:
        flash('Category name cannot be empty.', 'danger')
        return redirect(url_for('admin.categories', action='edit', id=id))

    # Check for name uniqueness with other categories
    existing = Category.query.filter(Category.name == name, Category.id != id).first()
    if existing:
        flash(f'Another category already has the name "{name}".', 'warning')
        return redirect(url_for('admin.categories', action='edit', id=id))

    category.name = name

    # Update image if new URL provided
    if img_url:
        category.img = img_url

    # Update image if new file uploaded
    if img_file and img_file.filename:
        if allowed_file(img_file.filename):
            ext = img_file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"cat_{uuid.uuid4().hex[:10]}.{ext}"
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            img_file.save(save_path)
            category.img = f"/{UPLOAD_FOLDER}/{unique_filename}"
        else:
            flash('Invalid image format. Keeping previous category image.', 'warning')

    db.session.commit()
    flash(f'Category "{category.name}" updated successfully.', 'success')
    return redirect(url_for('admin.categories'))

@admin_db.route('/categories/delete/<int:id>', methods=['POST'])
@login_required
@limiter.exempt
def delete_category(id):
    category = Category.query.get_or_404(id)

    # Protect against deleting category with attached products
    if category.products and len(category.products) > 0:
        flash(f'Cannot delete category "{category.name}" because {len(category.products)} product(s) are linked to it. Please reassign or delete the products first.', 'danger')
        return redirect(url_for('admin.categories'))

    cat_name = category.name
    db.session.delete(category)
    db.session.commit()
    flash(f'Category "{cat_name}" deleted successfully.', 'success')
    return redirect(url_for('admin.categories'))