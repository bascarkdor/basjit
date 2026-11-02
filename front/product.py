from flask import render_template, request, make_response, abort
from . import user_db
from models.product import Product
from models.category import Category
from extensions import db

@user_db.route('/products')
def view_products():
    search_query = request.args.get('search', '').strip()
    selected_category = request.args.get('category', '').strip()
    sort_by = request.args.get('sort', '').strip()

    query = Product.query.filter(Product.status != 'inactive')

    # Filter by search
    if search_query:
        query = query.filter(
            db.or_(
                Product.title.ilike(f'%{search_query}%'),
                Product.description.ilike(f'%{search_query}%'),
                Product.name.ilike(f'%{search_query}%')
            )
        )

    # Filter by category (either by ID or by name)
    if selected_category:
        if selected_category.isdigit():
            query = query.filter(Product.category_id == int(selected_category))
        else:
            query = query.join(Product.category).filter(Category.name.ilike(selected_category))

    # Sorting
    if sort_by == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'rating':
        query = query.order_by(Product.rating_rate.desc())
    else:
        query = query.order_by(Product.id.desc())

    products_list = query.all()
    categories_list = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        'user/page/product.html',
        products=products_list,
        categories=categories_list,
        selected_category=selected_category,
        search_query=search_query,
        sort_by=sort_by
    )

@user_db.route('/product')
def product_detail():
    product_id = request.args.get('id', type=int)

    if not product_id:
        return "Product ID is required", 400

    product = Product.query.get(product_id)
    if product is None:
        abort(404)

    # Fetch related products from the same category
    if product.category_id:
        related_products = Product.query.filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.status != 'inactive'
        ).limit(4).all()
    else:
        related_products = Product.query.filter(
            Product.id != product.id,
            Product.status != 'inactive'
        ).limit(4).all()

    existing_cart = request.cookies.get('shopping_cart', '')
    is_adding = request.args.get('add', type=bool, default=False)

    response = make_response(
        render_template(
            'user/page/product_detail.html',
            product=product,
            related_products=related_products
        )
    )

    if is_adding:
        if existing_cart:
            updated_cart = f"{existing_cart},{product_id}"
        else:
            updated_cart = str(product_id)

        response.set_cookie('shopping_cart', updated_cart, max_age=2592000)

    return response