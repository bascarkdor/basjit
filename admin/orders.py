from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from extensions import db, limiter, csrf
from models.order import Order, OrderItem
from services.bakong_service import bakong_service
from . import admin_db

@admin_db.route('/orders', methods=['GET'])
@login_required
@limiter.exempt
def list_orders():
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    payment_status_filter = request.args.get('payment_status', '').strip()
    payment_method_filter = request.args.get('payment_method', '').strip()

    # Base query: Exclude KHQR orders with PENDING status (do not show pending KHQR)
    query = Order.query.filter(~db.and_(Order.payment_method == 'KHQR', Order.payment_status == 'PENDING'))

    if search_query:
        query = query.filter(
            db.or_(
                Order.order_number.ilike(f'%{search_query}%'),
                Order.customer_name.ilike(f'%{search_query}%'),
                Order.customer_phone.ilike(f'%{search_query}%'),
                Order.md5.ilike(f'%{search_query}%')
            )
        )

    if status_filter:
        query = query.filter(Order.order_status == status_filter)

    if payment_status_filter:
        query = query.filter(Order.payment_status == payment_status_filter)

    if payment_method_filter:
        query = query.filter(Order.payment_method == payment_method_filter)

    orders = query.order_by(Order.id.desc()).all()

    # KPI Statistics (excluding pending KHQR orders)
    total_orders = Order.query.filter(~db.and_(Order.payment_method == 'KHQR', Order.payment_status == 'PENDING')).count()
    khqr_orders_count = Order.query.filter(Order.payment_method == 'KHQR', Order.payment_status == 'PAID').count()
    delivery_orders_count = Order.query.filter_by(payment_method='DELIVERY').count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).filter_by(payment_status='PAID').scalar() or 0.0

    return render_template(
        'admin/page/orders.html',
        orders=orders,
        active_tab='all',
        title="All Orders",
        search_query=search_query,
        status_filter=status_filter,
        payment_status_filter=payment_status_filter,
        total_orders=total_orders,
        khqr_orders_count=khqr_orders_count,
        delivery_orders_count=delivery_orders_count,
        total_revenue=total_revenue
    )


@admin_db.route('/orders/delivery', methods=['GET'])
@login_required
@limiter.exempt
def delivery_orders():
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = Order.query.filter(Order.payment_method == 'DELIVERY')

    if search_query:
        query = query.filter(
            db.or_(
                Order.order_number.ilike(f'%{search_query}%'),
                Order.customer_name.ilike(f'%{search_query}%'),
                Order.customer_phone.ilike(f'%{search_query}%')
            )
        )

    if status_filter:
        query = query.filter(Order.order_status == status_filter)

    orders = query.order_by(Order.id.desc()).all()

    delivery_count = len(orders)
    total_delivery_amount = sum(o.total_amount for o in orders)

    return render_template(
        'admin/page/orders.html',
        orders=orders,
        active_tab='delivery',
        title="Pay with Delivery Orders",
        search_query=search_query,
        status_filter=status_filter,
        delivery_count=delivery_count,
        total_delivery_amount=total_delivery_amount
    )


@admin_db.route('/orders/khqr', methods=['GET'])
@login_required
@limiter.exempt
def khqr_orders():
    search_query = request.args.get('search', '').strip()

    # Only show PAID KHQR orders (do not show PENDING)
    query = Order.query.filter(Order.payment_method == 'KHQR', Order.payment_status == 'PAID')

    if search_query:
        query = query.filter(
            db.or_(
                Order.order_number.ilike(f'%{search_query}%'),
                Order.customer_name.ilike(f'%{search_query}%'),
                Order.customer_phone.ilike(f'%{search_query}%'),
                Order.md5.ilike(f'%{search_query}%')
            )
        )

    orders = query.order_by(Order.id.desc()).all()

    khqr_count = len(orders)
    khqr_paid_count = len(orders)
    khqr_paid_revenue = sum(o.total_amount for o in orders)

    return render_template(
        'admin/page/orders.html',
        orders=orders,
        active_tab='khqr',
        title="Pay with Bakong KHQR Orders",
        search_query=search_query,
        khqr_count=khqr_count,
        khqr_paid_count=khqr_paid_count,
        khqr_paid_revenue=khqr_paid_revenue
    )


@admin_db.route('/orders/<int:id>/status', methods=['POST'])
@login_required
@limiter.exempt
@csrf.exempt
def update_order_status(id):

    order = Order.query.get_or_404(id)

    # Status cannot be changed for Bakong KHQR orders
    if order.payment_method == 'KHQR':
        flash("Status cannot be changed for Bakong KHQR orders. KHQR transactions are verified automatically.", "warning")
        return redirect(request.referrer or url_for('admin.list_orders'))

    order_status = request.form.get('order_status')
    payment_status = request.form.get('payment_status')

    if order_status:
        order.order_status = order_status
    if payment_status:
        order.payment_status = payment_status

    db.session.commit()
    flash(f"Order #{order.order_number} status updated successfully.", "success")
    return redirect(request.referrer or url_for('admin.list_orders'))


@admin_db.route('/orders/<int:id>/verify-bakong', methods=['POST'])
@login_required
@limiter.exempt
def verify_order_bakong(id):
    order = Order.query.get_or_404(id)
    if not order.md5:
        flash("Order does not have a Bakong MD5 hash to verify.", "warning")
        return redirect(request.referrer or url_for('admin.khqr_orders'))

    result = bakong_service.check_transaction(order.md5)

    if result.get('paid'):
        order.payment_status = 'PAID'
        order.transaction_hash = result.get('transaction_hash') or order.transaction_hash
        order.external_ref = result.get('external_ref') or order.external_ref
        db.session.commit()
        flash(f"✅ Bakong Verification Success! Order #{order.order_number} is confirmed PAID.", "success")
    else:
        flash(f"ℹ️ Bakong API check: {result.get('message', 'Transaction not found or pending.')}", "info")

    return redirect(request.referrer or url_for('admin.khqr_orders'))


@admin_db.route('/orders/<int:id>/detail', methods=['GET'])
@login_required
@limiter.exempt
def order_detail(id):
    order = Order.query.get_or_404(id)
    return jsonify({
        "status": "success",
        "order": order.to_dict()
    })


@admin_db.route('/orders/<int:id>/delete', methods=['POST'])
@login_required
@limiter.exempt
def delete_order(id):
    order = Order.query.get_or_404(id)
    order_num = order.order_number
    db.session.delete(order)
    db.session.commit()
    flash(f"Order #{order_num} has been deleted.", "success")
    return redirect(request.referrer or url_for('admin.list_orders'))
