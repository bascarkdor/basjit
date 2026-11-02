from datetime import datetime
from extensions import db

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    img = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Links category to products using string reference to prevent circular imports
    products = db.relationship('Product', backref='category', lazy=True)

    @property
    def image(self):
        if self.img:
            return self.img
        # Curated high quality placeholder
        return "https://images.unsplash.com/photo-1472851294608-062f824d29cc?w=400&auto=format&fit=crop&q=60"

    @property
    def product_count(self):
        return len(self.products) if self.products else 0

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Category {self.name}>"
