from datetime import datetime
from extensions import db

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    # Customer Details
    customer_name = db.Column(db.String(120), nullable=False)
    customer_age = db.Column(db.Integer, nullable=True)
    customer_phone = db.Column(db.String(50), nullable=False)
    customer_location = db.Column(db.String(120), nullable=True)
    customer_address = db.Column(db.Text, nullable=False)

    # Order & Payment Amounts
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    currency = db.Column(db.String(10), default='USD')

    # Payment Info
    payment_method = db.Column(db.String(30), nullable=False, default='DELIVERY')  # 'KHQR' or 'DELIVERY'
    payment_status = db.Column(db.String(30), nullable=False, default='PENDING')   # 'PENDING', 'PAID', 'FAILED'
    order_status = db.Column(db.String(30), nullable=False, default='PENDING')     # 'PENDING', 'PROCESSING', 'COMPLETED', 'CANCELLED'

    # Bakong KHQR Fields
    md5 = db.Column(db.String(64), nullable=True, index=True)
    qr_string = db.Column(db.Text, nullable=True)
    transaction_hash = db.Column(db.String(128), nullable=True)
    external_ref = db.Column(db.String(128), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    @property
    def is_paid(self):
        return self.payment_status == 'PAID'

    def to_dict(self):
        return {
            "id": self.id,
            "order_number": self.order_number,
            "customer_name": self.customer_name,
            "customer_age": self.customer_age,
            "customer_phone": self.customer_phone,
            "customer_location": self.customer_location,
            "customer_address": self.customer_address,
            "total_amount": self.total_amount,
            "currency": self.currency,
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "order_status": self.order_status,
            "md5": self.md5,
            "transaction_hash": self.transaction_hash,
            "external_ref": self.external_ref,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            "items": [item.to_dict() for item in self.items]
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='SET NULL'), nullable=True)
    product_title = db.Column(db.String(255), nullable=False)
    product_price = db.Column(db.Float, nullable=False, default=0.0)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)

    # Relationship to product
    product = db.relationship('Product', backref='order_items', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_title": self.product_title,
            "product_price": self.product_price,
            "quantity": self.quantity,
            "subtotal": self.subtotal
        }
