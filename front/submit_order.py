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