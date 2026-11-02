from app import app
from extensions import db
from models.category import Category

images = {
    "men's clothing": "https://images.unsplash.com/photo-1490578474895-699cd4e2cf59?w=300&auto=format&fit=crop&q=80",
    "jewelery": "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=300&auto=format&fit=crop&q=80",
    "electronics": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=300&auto=format&fit=crop&q=80",
    "women's clothing": "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=300&auto=format&fit=crop&q=80"
}

with app.app_context():
    cats = Category.query.all()
    for c in cats:
        if not c.img and c.name in images:
            c.img = images[c.name]
            print(f"Updated {c.name} -> {c.img}")
    db.session.commit()
    print("Done updating category images!")
