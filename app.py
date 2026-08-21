import requests
from flask import Flask, render_template, request, make_response, redirect, session, url_for, flash
from flask_login import LoginManager

from config import Config
from extensions import db, migrate
from data import products
import admin
from models.user import User

app = Flask(__name__)

# Load database settings from config.py
app.config.from_object(Config)

# Attach extensions to Flask app
db.init_app(app)
migrate.init_app(app, db)  # <-- This adds the 'flask db' command

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
# Redirect unauthenticated users trying to access protected routes
login_manager.login_view = 'admin.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(admin.admin_db, url_prefix='/admin')

TELEGRAM_BOT_TOKEN = "8218708595:AAH2GIYkr7Q4OiC72CnYqn8-qcgB5g8Dz0o"
TELEGRAM_CHAT_ID = "-1003855315911"

# --- User Routes ---

@app.route('/')
def home():
    return render_template('user/page/home.html', product_list=products)

@app.route('/products')
def view_products():
    return render_template('user/page/product.html', products=products)

@app.route('/cart')
def cart():
    cart_cookie = request.cookies.get('shopping_cart', '')
    cart_ids = [int(item_id) for item_id in cart_cookie.split(',') if item_id]

    id_counts = {}
    for item_id in cart_ids:
        id_counts[item_id] = id_counts.get(item_id, 0) + 1

    cart_list = []
    for item_id, qty in id_counts.items():
        matched_item = next((p for p in products if p['id'] == item_id), None)
        if matched_item:
            cart_list.append({
                "id": matched_item["id"],
                "title": matched_item["title"],
                "price": matched_item["price"],
                "image": matched_item["image"],
                "category": matched_item["category"],
                "qty": qty,
                "row_total": matched_item["price"] * qty
            })

    grand_total = sum(item['row_total'] for item in cart_list)
    return render_template('user/page/view-cart.html', cart=cart_list, total=grand_total)

@app.route('/product')
def product_detail():
    product_id = request.args.get('id', type=int)

    if not product_id:
        return "Product ID is required", 400

    product = next((p for p in products if p['id'] == product_id), None)

    if product is None:
        return "Product Not Found", 404

    related_products = [
        p for p in products
        if p['category'] == product['category'] and p['id'] != product['id']
    ]

    existing_cart = request.cookies.get('shopping_cart', '')
    is_adding = request.args.get('add', type=bool, default=False)

    response = make_response(
        render_template('user/page/product_detail.html', product=product, related_products=related_products)
    )

    if is_adding:
        if existing_cart:
            updated_cart = f"{existing_cart},{product_id}"
        else:
            updated_cart = str(product_id)

        response.set_cookie('shopping_cart', updated_cart, max_age=2592000)

    return response

@app.route('/cart/add')
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

@app.route('/cart/update', methods=['POST'])
def update_cart():
    product_id = request.form.get('product_id', type=int)
    action = request.form.get('action')

    if not product_id:
        return redirect('/cart')

    cart_cookie = request.cookies.get('shopping_cart', '')
    cart_ids = [int(item_id) for item_id in cart_cookie.split(',') if item_id]

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

@app.route('/checkout', methods=['POST'])
def checkout():
    cart_cookie = request.cookies.get('shopping_cart', '')

    if not cart_cookie:
        flash("Your cart is empty!", "warning")
        return redirect('/products')

    cart_ids = [int(item_id) for item_id in cart_cookie.split(',') if item_id]

    id_counts = {}
    for item_id in cart_ids:
        id_counts[item_id] = id_counts.get(item_id, 0) + 1

    cart_list = []
    grand_total = 0.0

    for item_id, qty in id_counts.items():
        matched_item = next((p for p in products if p['id'] == item_id), None)
        if matched_item:
            row_total = matched_item["price"] * qty
            grand_total += row_total
            cart_list.append({
                "title": matched_item["title"],
                "price": matched_item["price"],
                "qty": qty,
                "row_total": row_total
            })

    if not cart_list:
        flash("Your cart items are invalid!", "warning")
        return redirect('/products')

    return render_template('user/page/checkout.html', total=grand_total)

@app.route('/submit-order', methods=['POST'])
def submit_order():
    cart_cookie = request.cookies.get('shopping_cart', '')
    if not cart_cookie:
        flash("Your cart session has expired.", "error")
        return redirect('/products')

    cart_ids = [int(item_id) for item_id in cart_cookie.split(',') if item_id]

    id_counts = {}
    for item_id in cart_ids:
        id_counts[item_id] = id_counts.get(item_id, 0) + 1

    username = request.form.get('username')
    age = request.form.get('age')
    phone = request.form.get('phone')
    location = request.form.get('location')
    address = request.form.get('address')

    items_summary = ""
    grand_total = 0.0

    for item_id, qty in id_counts.items():
        matched_item = next((p for p in products if p['id'] == item_id), None)
        if matched_item:
            row_total = matched_item["price"] * qty
            grand_total += row_total
            items_summary += f"📦 *{matched_item['title']}*\n"
            items_summary += f"   ↳ Qty: {qty} x ${matched_item['price']:.2f} = ${row_total:.2f}\n"

    message = (
        f"🚨 📈 *NEW INCOMING ORDER* 📈 🚨\n\n"
        f"👤 *Customer Profile:*\n"
        f"• **Name:** {username}\n"
        f"• **Age:** {age}\n"
        f"• **Phone:** {phone}\n\n"
        f"📍 *Delivery Destination:*\n"
        f"• **Region/City:** {location}\n"
        f"• **Full Address:**\n{address}\n\n"
        f"🛒 *Line Items Ordered:*\n"
        f"{items_summary}\n"
        f"💰 **GRAND TOTAL AMOUNT: ${grand_total:.2f}**"
    )

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        api_response = requests.post(telegram_url, json=payload)
        if api_response.status_code == 200:
            response = make_response(redirect(url_for('payment_success')))
            response.delete_cookie('shopping_cart')
            return response
        else:
            return f"Telegram API Error: {api_response.text}", 400

    except Exception as e:
        return f"Failed to send order notification: {str(e)}", 500

@app.route('/payment_success')
def payment_success():
    return render_template('user/page/susccess_payment.html')

@app.route('/about')
def about():
    return render_template('user/page/about.html')

@app.route('/contact')
def contact():
    return render_template('user/page/contact.html')

@app.route('/register')
def register():
    return render_template('user/page/register.html')

@app.route('/login')
def login():
    return render_template('user/page/login.html')

@app.route('/settings')
def settings():
    return render_template('user/page/setting.html')

if __name__ == '__main__':
    app.run(debug=True)