import os
import uuid
from flask import render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask_login import login_required
from extensions import db
from models.product import Product
from models.ProductImage import ProductImage
from models.category import Category
from . import admin_db
from extensions import limiter

UPLOAD_FOLDER = 'static/uploads/products'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_db.route('/product', methods=['GET'])
@login_required
@limiter.exempt
def product():
    action = request.args.get('action')
    product_id = request.args.get('id', type=int)
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)
    stock_status = request.args.get('stock_status', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 12

    # Pure Python server-side edit retrieval
    edit_product = None
    if action == 'edit' and product_id:
        edit_product = Product.query.get(product_id)

    query = Product.query

    # Search filter
    if search:
        query = query.filter(
            db.or_(
                Product.title.ilike(f'%{search}%'),
                Product.name.ilike(f'%{search}%'),
                Product.description.ilike(f'%{search}%')
            )
        )

    # Category filter
    if category_id:
        query = query.filter(Product.category_id == category_id)

    # Stock status filter
    if stock_status == 'in_stock':
        query = query.filter(Product.status == 'active', Product.stock != '0')
    elif stock_status == 'out_of_stock':
        query = query.filter(db.or_(Product.stock == '0', Product.status == 'out_of_stock'))
    elif stock_status == 'low_stock':
        query = query.filter(Product.stock.in_(['1', '2', '3', '4', '5']))

    # Order by newest
    query = query.order_by(Product.id.desc())

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products_list = pagination.items
    categories_list = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        'admin/page/product.html',
        products=products_list,
        categories=categories_list,
        pagination=pagination,
        search=search,
        selected_category_id=category_id,
        selected_stock_status=stock_status,
        edit_product=edit_product
    )


@admin_db.route('/product/add', methods=['POST'])
@login_required
@limiter.exempt
def add_product():
    title = request.form.get('title', '').strip()
    name = request.form.get('name', '').strip() or title
    category_id = request.form.get('category_id', type=int)
    price = request.form.get('price', type=float, default=0.0)
    discount_price = request.form.get('discount_price', '').strip() or None
    stock = request.form.get('stock', '').strip() or '0'
    status = request.form.get('status', 'active').strip()
    description = request.form.get('description', '').strip()
    rating_rate = request.form.get('rating_rate', type=float, default=0.0)
    rating_count = request.form.get('rating_count', type=int, default=0)
    image_url = request.form.get('image_url', '').strip()

    if not title:
        flash('Product title is required.', 'danger')
        return redirect(url_for('admin.product', action='add'))

    thumbnail_path = image_url if image_url else None
    uploaded_image_paths = []

    # Handle multiple image files upload
    files = request.files.getlist('product_images')
    if not any(f.filename for f in files):
        single_file = request.files.get('product_image')
        if single_file and single_file.filename:
            files = [single_file]

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    for file in files:
        if file and file.filename != '' and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            clean_base = secure_filename(file.filename.rsplit('.', 1)[0]) or 'image'
            unique_name = f"{uuid.uuid4().hex[:12]}_{clean_base}.{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, unique_name)
            file.save(filepath)
            path_str = f"/{UPLOAD_FOLDER}/{unique_name}"
            uploaded_image_paths.append(path_str)

    # First uploaded file becomes thumbnail if none provided
    if not thumbnail_path and uploaded_image_paths:
        thumbnail_path = uploaded_image_paths[0]

    new_prod = Product(
        title=title,
        name=name,
        category_id=category_id if category_id and category_id > 0 else None,
        price=price,
        discount_price=discount_price,
        stock=stock,
        status=status,
        description=description,
        rating_rate=rating_rate,
        rating_count=rating_count,
        thumbnail=thumbnail_path
    )

    db.session.add(new_prod)
    db.session.flush()

    # Save additional images into ProductImage gallery
    for img_path in uploaded_image_paths:
        gallery_img = ProductImage(product_id=new_prod.id, name=img_path)
        db.session.add(gallery_img)

    db.session.commit()
    flash(f'Product "{title}" created with {len(uploaded_image_paths)} image(s).', 'success')
    return redirect(url_for('admin.product'))


@admin_db.route('/product/edit/<int:id>', methods=['POST'])
@login_required
@limiter.exempt
def edit_product(id):
    prod = Product.query.get_or_404(id)

    title = request.form.get('title', '').strip()
    if not title:
        flash('Product title is required.', 'danger')
        return redirect(url_for('admin.product', action='edit', id=id))

    prod.title = title
    prod.name = request.form.get('name', '').strip() or prod.title
    category_id = request.form.get('category_id', type=int)
    prod.category_id = category_id if category_id and category_id > 0 else None

    price = request.form.get('price', type=float)
    if price is not None:
        prod.price = price

    prod.discount_price = request.form.get('discount_price', '').strip() or None
    prod.stock = request.form.get('stock', '').strip() or '0'
    prod.status = request.form.get('status', prod.status).strip()
    prod.description = request.form.get('description', '').strip()

    rating_rate = request.form.get('rating_rate', type=float)
    if rating_rate is not None:
        prod.rating_rate = rating_rate

    rating_count = request.form.get('rating_count', type=int)
    if rating_count is not None:
        prod.rating_count = rating_count

    image_url = request.form.get('image_url', '').strip()
    if image_url:
        prod.thumbnail = image_url

    # Check for multiple file uploads
    files = request.files.getlist('product_images')
    if not any(f.filename for f in files):
        single_file = request.files.get('product_image')
        if single_file and single_file.filename:
            files = [single_file]

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    new_images_count = 0
    for file in files:
        if file and file.filename != '' and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            clean_base = secure_filename(file.filename.rsplit('.', 1)[0]) or 'image'
            unique_name = f"{uuid.uuid4().hex[:12]}_{clean_base}.{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, unique_name)
            file.save(filepath)
            saved_path = f"/{UPLOAD_FOLDER}/{unique_name}"
            
            # If product has no thumbnail yet, set this one
            if not prod.thumbnail:
                prod.thumbnail = saved_path

            # Add to ProductImage gallery
            gallery_img = ProductImage(product_id=prod.id, name=saved_path)
            db.session.add(gallery_img)
            new_images_count += 1

    db.session.commit()
    msg = f'Product "{prod.title}" updated successfully.'
    if new_images_count > 0:
        msg += f' Added {new_images_count} new image(s).'
    flash(msg, 'success')
    return redirect(url_for('admin.product', action='edit', id=id))


@admin_db.route('/product/image/delete/<int:image_id>', methods=['POST'])
@login_required
@limiter.exempt
def delete_product_image(image_id):
    image = ProductImage.query.get_or_404(image_id)
    product_id = image.product_id

    # If this image was also set as the main thumbnail, clear or reassign it
    product = Product.query.get(product_id)
    if product and product.thumbnail == image.name:
        other_img = ProductImage.query.filter(ProductImage.product_id == product_id, ProductImage.id != image.id).first()
        product.thumbnail = other_img.name if other_img else None

    db.session.delete(image)
    db.session.commit()
    flash('Gallery image removed successfully.', 'info')
    return redirect(url_for('admin.product', action='edit', id=product_id))


@admin_db.route('/product/delete/<int:id>', methods=['POST'])
@login_required
@limiter.exempt
def delete_product(id):
    prod = Product.query.get_or_404(id)
    title = prod.title
    db.session.delete(prod)
    db.session.commit()
    flash(f'Product "{title}" deleted successfully.', 'success')
    return redirect(url_for('admin.product'))