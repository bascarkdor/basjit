from datetime import datetime
from extensions import db

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    stock = db.Column(db.String(120), nullable=True, default='0')
    thumbnail = db.Column(db.String(500), nullable=True)
    price = db.Column(db.Float, nullable=True, default=0.0)
    status = db.Column(db.String(50), nullable=False, default='active')
    discount_price = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)  
    
    # Rating fields
    rating_rate = db.Column(db.Float, nullable=True, default=0.0)
    rating_count = db.Column(db.Integer, nullable=True, default=0)

    # Foreign Key linking to the categories table
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    
    # Relationship to product images
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def display_title(self):
        return self.title or self.name or "Untitled Product"

    @property
    def image(self):
        if self.thumbnail:
            return self.thumbnail
        if self.images and len(self.images) > 0:
            return self.images[0].name
        return "https://th.bing.com/th/id/OIP.LsDRHNPePGHV1voFALvicgHaFB?w=270&h=183&c=7&r=0&o=7&pid=1.7&rm=3"

    @property
    def all_images(self):
        result = []
        if self.thumbnail:
            result.append(self.thumbnail)
        for img in self.images:
            if img.name not in result:
                result.append(img.name)
        if not result:
            result.append("https://th.bing.com/th/id/OIP.LsDRHNPePGHV1voFALvicgHaFB?w=270&h=183&c=7&r=0&o=7&pid=1.7&rm=3")
        return result

    @property
    def rating(self):
        return {
            'rate': round(float(self.rating_rate or 0.0), 1),
            'count': int(self.rating_count or 0)
        }

    @property
    def stock_int(self):
        try:
            return int(self.stock) if self.stock is not None else 0
        except (ValueError, TypeError):
            return 0

    @property
    def category_name(self):
        return self.category.name if self.category else "Uncategorized"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "name": self.name or self.title,
            "stock": self.stock or "0",
            "stock_int": self.stock_int,
            "thumbnail": self.thumbnail or "",
            "image": self.image,
            "price": self.price or 0.0,
            "discount_price": self.discount_price or "",
            "status": self.status or "active",
            "description": self.description or "",
            "rating_rate": self.rating_rate or 0.0,
            "rating_count": self.rating_count or 0,
            "rating": self.rating,
            "category_id": self.category_id,
            "category": self.category_name,
            "images": [img.name for img in self.images] if self.images else []
        }