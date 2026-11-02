import requests

TELEGRAM_BOT_TOKEN = "8218708595:AAH2GIYkr7Q4OiC72CnYqn8-qcgB5g8Dz0o"
TELEGRAM_CHAT_ID = "-1003855315911"

def send_order_notification(order):
    """
    Sends a rich formatted order notification to Telegram group/chat.
    """
    items_summary = ""
    for item in order.items:
        items_summary += f"📦 *{item.product_title}*\n"
        items_summary += f"   ↳ Qty: {item.quantity} x ${item.product_price:.2f} = ${item.subtotal:.2f}\n"

    payment_badge = "🇰🇭 *BAKONG KHQR (PAID)* ✅" if order.payment_method == 'KHQR' else "🚚 *CASH ON DELIVERY (PENDING)* ⏳"

    extra_info = ""
    if order.payment_method == 'KHQR':
        if order.transaction_hash:
            extra_info += f"• **Tx Hash / Ref:** `{order.transaction_hash}`\n"
        if order.md5:
            extra_info += f"• **MD5:** `{order.md5}`\n"

    message = (
        f"🚨 📈 *NEW INCOMING ORDER: {order.order_number}* 📈 🚨\n\n"
        f"💳 **Payment Method:** {payment_badge}\n"
        f"📊 **Payment Status:** *{order.payment_status}*\n"
        f"{extra_info}\n"
        f"👤 *Customer Profile:*\n"
        f"• **Name:** {order.customer_name}\n"
        f"• **Age:** {order.customer_age or 'N/A'}\n"
        f"• **Phone:** {order.customer_phone}\n\n"
        f"📍 *Delivery Destination:*\n"
        f"• **Region/City:** {order.customer_location or 'N/A'}\n"
        f"• **Full Address:**\n{order.customer_address}\n\n"
        f"🛒 *Line Items Ordered:*\n"
        f"{items_summary}\n"
        f"💰 **GRAND TOTAL AMOUNT: ${order.total_amount:.2f} {order.currency}**"
    )

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        requests.post(telegram_url, json=payload, timeout=5)
    except Exception as e:
        print(f"Failed to send Telegram notification: {e}")
