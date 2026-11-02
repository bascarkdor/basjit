import uuid
from datetime import datetime
from flask import request, make_response, redirect, url_for, flash, jsonify, session
from flask_login import current_user
from . import user_db
from extensions import db, csrf
from models.product import Product
from models.order import Order, OrderItem
from services.bakong_service import bakong_service
from services.telegram_service import send_order_notification

# In-memory store for pending KHQR orders waiting for payment verification
# Orders are NEVER written to the database until Bakong confirms payment (PAID)
_PENDING_KHQR_ORDERS = {}

def _get_cart_items_and_total():
    cart_cookie = request.cookies.get('shopping_cart', '')
    if not cart_cookie:
        return None, 0.0

    cart_ids = [int(item_id) for item_id in cart_cookie.split(',') if item_id.isdigit()]
    if not cart_ids:
        return None, 0.0

    id_counts = {}
    for item_id in cart_ids:
        id_counts[item_id] = id_counts.get(item_id, 0) + 1

    items = []
    grand_total = 0.0

    for item_id, qty in id_counts.items():
        matched_item = Product.query.get(item_id)
        if matched_item:
            price = float(matched_item.price or 0.0)
            row_total = price * qty
            grand_total += row_total
            items.append({
                "product": matched_item,
                "price": price,
                "qty": qty,
                "subtotal": row_total
            })

    return items, grand_total


@user_db.route('/submit-order', methods=['POST'])
@csrf.exempt
def submit_order():
    """
    Handles standard checkout submission, typically for 'DELIVERY' (Cash on Delivery).
    """
    if not current_user.is_authenticated:
        flash("Please log in or register before checking out and paying for your order.", "warning")
        return redirect(url_for('.login', next=url_for('.checkout')))

    items, grand_total = _get_cart_items_and_total()
    if not items:
        flash("Your cart session has expired or is empty.", "error")
        return redirect('/products')

    username = request.form.get('username', '').strip()
    age = request.form.get('age', type=int)
    phone = request.form.get('phone', '').strip()
    location = request.form.get('location', '').strip()
    address = request.form.get('address', '').strip()
    payment_method = request.form.get('payment_method', 'DELIVERY').upper()

    if not username or not phone or not address:
        flash("Please fill in all required customer details.", "warning")
        return redirect('/checkout')

    order_number = f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"

    order = Order(
        order_number=order_number,
        customer_name=username,
        customer_age=age,
        customer_phone=phone,
        customer_location=location,
        customer_address=address,
        total_amount=grand_total,
        currency="USD",
        payment_method=payment_method,
        payment_status="PENDING",
        order_status="PENDING"
    )

    for item in items:
        order_item = OrderItem(
            order=order,
            product_id=item['product'].id,
            product_title=item['product'].display_title,
            product_price=item['price'],
            quantity=item['qty'],
            subtotal=item['subtotal']
        )
        db.session.add(order_item)

    db.session.add(order)
    db.session.commit()

    # Dispatch Telegram Alert
    send_order_notification(order)

    # Redirect to success page and clear shopping cart cookie
    response = make_response(redirect(url_for('.payment_success', order_id=order.id)))
    response.delete_cookie('shopping_cart')
    return response


@user_db.route('/api/checkout/create-khqr-order', methods=['POST'])
@csrf.exempt
def create_khqr_order():
    """
    Generates dynamic KHQR payload and MD5 hash.
    NOTE: Does NOT store the order into the database when status is PENDING!
    Order is kept in transient memory/session and only committed to DB once PAID.
    """
    if not current_user.is_authenticated:
        return jsonify({
            "status": "error",
            "require_auth": True,
            "message": "Login or registration is required before paying for your order.",
            "redirect_url": url_for('.login', next=url_for('.checkout'))
        }), 401

    items, grand_total = _get_cart_items_and_total()
    if not items:
        return jsonify({"status": "error", "message": "Your cart is empty."}), 400

    data = request.get_json(silent=True) or request.form
    username = data.get('username', '').strip()
    age = data.get('age')
    try:
        age = int(age) if age else None
    except (ValueError, TypeError):
        age = None
    phone = data.get('phone', '').strip()
    location = data.get('location', '').strip()
    address = data.get('address', '').strip()

    if not username or not phone or not address:
        return jsonify({"status": "error", "message": "Please provide your Name, Phone Number, and Address."}), 400

    order_number = f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"

    try:
        # Generate Bakong KHQR payload & QR PNG base64
        khqr_data = bakong_service.generate_khqr(order_number, grand_total, "USD")
    except Exception as e:
        return jsonify({"status": "error", "message": f"Could not generate KHQR: {str(e)}"}), 500

    md5_hash = khqr_data["md5"]

    # Store order details in transient memory / session ONLY (not in DB while pending)
    items_data = []
    for item in items:
        items_data.append({
            "product_id": item['product'].id,
            "product_title": item['product'].display_title,
            "product_price": item['price'],
            "quantity": item['qty'],
            "subtotal": item['subtotal']
        })

    pending_order_info = {
        "order_number": order_number,
        "username": username,
        "age": age,
        "phone": phone,
        "location": location,
        "address": address,
        "total_amount": grand_total,
        "currency": "USD",
        "payment_method": "KHQR",
        "md5": md5_hash,
        "qr_string": khqr_data["qr_string"],
        "items": items_data
    }

    _PENDING_KHQR_ORDERS[md5_hash] = pending_order_info
    session['pending_khqr_order'] = pending_order_info

    # Return QR details to frontend WITHOUT writing to database
    return jsonify({
        "status": "success",
        "order_number": order_number,
        "md5": md5_hash,
        "qr_image": khqr_data["qr_image"],
        "amount": khqr_data["amount"],
        "currency": khqr_data["currency"],
        "merchant_name": khqr_data["merchant_name"]
    })


@user_db.route('/api/bakong/check-status', methods=['GET', 'POST'])
@csrf.exempt
def check_bakong_status():
    """
    Checks if transaction is paid via MD5 hash.
    Polled every 3 seconds by the client frontend popup.
    ONLY stores the order into the DB once Bakong confirms payment (PAID).
    """
    data = request.get_json(silent=True) or request.values
    md5 = data.get('md5')

    if not md5:
        return jsonify({"paid": False, "message": "MD5 hash required"}), 400

    # 1. Check if already recorded as PAID in DB
    existing_order = Order.query.filter_by(md5=md5, payment_status='PAID').first()
    if existing_order:
        return jsonify({
            "paid": True,
            "message": "Payment verified!",
            "redirect_url": url_for('.payment_success', order_id=existing_order.id)
        })

    # 2. Call NBC Bakong API to check MD5 transaction status
    verify_result = bakong_service.check_transaction(md5)

    if verify_result.get("paid"):
        # Payment Captured! Retrieve pending order info to store in DB now
        pending = _PENDING_KHQR_ORDERS.get(md5) or session.get('pending_khqr_order')

        if not pending:
            # Fallback if session/memory cleared but payment received
            pending = {
                "order_number": f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}",
                "username": "Online Customer",
                "age": None,
                "phone": "N/A",
                "location": "Phnom Penh",
                "address": "Bakong KHQR Order",
                "total_amount": 0.0,
                "items": []
            }

        order = Order(
            order_number=pending.get('order_number'),
            customer_name=pending.get('username'),
            customer_age=pending.get('age'),
            customer_phone=pending.get('phone'),
            customer_location=pending.get('location'),
            customer_address=pending.get('address'),
            total_amount=pending.get('total_amount', 0.0),
            currency="USD",
            payment_method="KHQR",
            payment_status="PAID",
            order_status="PENDING",
            md5=md5,
            qr_string=pending.get('qr_string'),
            transaction_hash=verify_result.get("transaction_hash") or "",
            external_ref=verify_result.get("external_ref") or ""
        )

        for itm in pending.get('items', []):
            order_item = OrderItem(
                order=order,
                product_id=itm.get('product_id'),
                product_title=itm.get('product_title'),
                product_price=itm.get('product_price'),
                quantity=itm.get('quantity'),
                subtotal=itm.get('subtotal')
            )
            db.session.add(order_item)

        db.session.add(order)
        db.session.commit()

        # Remove from transient memory & session
        _PENDING_KHQR_ORDERS.pop(md5, None)
        session.pop('pending_khqr_order', None)

        # Dispatch Telegram notification for captured payment
        send_order_notification(order)

        return jsonify({
            "paid": True,
            "message": "Payment confirmed successfully by Bakong!",
            "redirect_url": url_for('.payment_success', order_id=order.id)
        })

    # While still pending, DO NOT store into database!
    return jsonify({
        "paid": False,
        "message": verify_result.get("message", "Awaiting payment...")
    })


@user_db.route('/api/bakong/simulate-payment', methods=['POST'])
@user_db.route('/api/bakong/simulate-payment/<path:param>', methods=['POST'])
@csrf.exempt
def simulate_bakong_payment(param=None):
    """
    Development/Testing endpoint to simulate a successful Bakong KHQR payment.
    Stores the order in the database ONLY as PAID.
    """
    data = request.get_json(silent=True) or request.values
    md5 = data.get('md5') or (param if param and not param.isdigit() else None)
    order_id = param if param and param.isdigit() else data.get('order_id')

    order = None
    if order_id:
        order = Order.query.get(int(order_id))

    if not order and md5:
        order = Order.query.filter_by(md5=md5).first()

    if not order and md5:
        # Create from pending memory/session and mark PAID
        pending = _PENDING_KHQR_ORDERS.get(md5) or session.get('pending_khqr_order')
        if pending:
            order = Order(
                order_number=pending.get('order_number'),
                customer_name=pending.get('username'),
                customer_age=pending.get('age'),
                customer_phone=pending.get('phone'),
                customer_location=pending.get('location'),
                customer_address=pending.get('address'),
                total_amount=pending.get('total_amount', 0.0),
                currency="USD",
                payment_method="KHQR",
                payment_status="PAID",
                order_status="PENDING",
                md5=md5,
                qr_string=pending.get('qr_string'),
                transaction_hash=f"SIM-{uuid.uuid4().hex[:12].upper()}",
                external_ref=f"SIM-REF-{uuid.uuid4().hex[:8].upper()}"
            )
            for itm in pending.get('items', []):
                order_item = OrderItem(
                    order=order,
                    product_id=itm.get('product_id'),
                    product_title=itm.get('product_title'),
                    product_price=itm.get('product_price'),
                    quantity=itm.get('quantity'),
                    subtotal=itm.get('subtotal')
                )
                db.session.add(order_item)

            db.session.add(order)
            db.session.commit()

            _PENDING_KHQR_ORDERS.pop(md5, None)
            session.pop('pending_khqr_order', None)
            send_order_notification(order)

            return jsonify({
                "paid": True,
                "message": "Simulated payment successful!",
                "redirect_url": url_for('.payment_success', order_id=order.id)
            })

    if order:
        order.payment_status = "PAID"
        order.transaction_hash = f"SIM-{uuid.uuid4().hex[:12].upper()}"
        order.external_ref = f"SIM-REF-{uuid.uuid4().hex[:8].upper()}"
        db.session.commit()
        send_order_notification(order)
        return jsonify({
            "paid": True,
            "message": "Simulated payment successful!",
            "redirect_url": url_for('.payment_success', order_id=order.id)
        })

    return jsonify({"paid": False, "message": "Pending order not found to simulate."}), 404