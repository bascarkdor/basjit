from flask import render_template, request, make_response, redirect
from . import user_db
from models.product import Product

@user_db.route('/cart')
def cart():
    cart_cookie = request.cookies.get('shopping_cart', '')
    cart_ids = [int(item_id) for item_id in cart_cookie.split(',') if item_id.isdigit()]

    id_counts = {}
    for item_id in cart_ids:
        id_counts[item_id] = id_counts.get(item_id, 0) + 1

    cart_list = []
    for item_id, qty in id_counts.items():
        matched_item = Product.query.get(item_id)
        if matched_item:
            price = float(matched_item.price or 0.0)
            cart_list.append({
                "id": matched_item.id,
                "title": matched_item.display_title,
                "price": price,
                "image": matched_item.image,
                "category": matched_item.category_name,
                "qty": qty,
                "row_total": price * qty
            })

    grand_total = sum(item['row_total'] for item in cart_list)
    return render_template('user/page/view-cart.html', cart=cart_list, total=grand_total)


@user_db.route('/cart/add')
def add_to_cart():
    product_id = request.args.get('id', type=int)
    if not product_id:
        return "Product ID is required", 400

    existing_cart = request.cookies.get('shopping_cart', '')

    if existing_cart:
        updated_cart = f"{existing_cart},{product_id}"
    else:
        updated_cart = str(product_id)

    response = make_response(redirect('/cart'))
    response.set_cookie('shopping_cart', updated_cart, max_age=2592000)

    return response


@user_db.route('/cart/update', methods=['POST'])
def update_cart():
    product_id = request.form.get('product_id', type=int)
    action = request.form.get('action')

    if not product_id:
        return redirect('/cart')

    cart_cookie = request.cookies.get('shopping_cart', '')
    cart_ids = [int(item_id) for item_id in cart_cookie.split(',') if item_id.isdigit()]

    if action == 'increase':
        cart_ids.append(product_id)
    elif action == 'decrease':
        if product_id in cart_ids:
            cart_ids.remove(product_id)

    updated_cookie_str = ",".join(map(str, cart_ids))

    response = make_response(redirect('/cart'))
    if updated_cookie_str:
        response.set_cookie('shopping_cart', updated_cookie_str, max_age=2592000)
    else:
        response.delete_cookie('shopping_cart')

    return response