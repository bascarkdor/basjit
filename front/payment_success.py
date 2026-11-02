from flask import render_template, request, make_response
from . import user_db
from models.order import Order

@user_db.route('/payment_success')
def payment_success():
    order_id = request.args.get('order_id', type=int)
    order = None
    if order_id:
        order = Order.query.get(order_id)

    response = make_response(render_template('user/page/susccess_payment.html', order=order))
    response.delete_cookie('shopping_cart')
    return response