from flask import render_template, request, flash, redirect, url_for
from flask_login import current_user
from . import user_db
from models.product import Product

@user_db.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if not current_user.is_authenticated:
        flash("Please log in or register before checking out and paying for your order.", "warning")
        return redirect(url_for('user.login', next=url_for('user.checkout')))

    cart_cookie = request.cookies.get('shopping_cart', '')

    if not cart_cookie:
        flash("Your cart is empty!", "warning")
        return redirect('/products')

    cart_ids = [int(item_id) for item_id in cart_cookie.split(',') if item_id.isdigit()]

    id_counts = {}
    for item_id in cart_ids:
        id_counts[item_id] = id_counts.get(item_id, 0) + 1

    cart_list = []
    grand_total = 0.0

    for item_id, qty in id_counts.items():
        matched_item = Product.query.get(item_id)
        if matched_item:
            price = float(matched_item.price or 0.0)
            row_total = price * qty
            grand_total += row_total
            cart_list.append({
                "id": matched_item.id,
                "title": matched_item.display_title,
                "price": price,
                "image": matched_item.image,
                "qty": qty,
                "row_total": row_total
            })

    if not cart_list:
        flash("Your cart items are invalid!", "warning")
        return redirect('/products')

    return render_template('user/page/checkout.html', cart_items=cart_list, total=grand_total)