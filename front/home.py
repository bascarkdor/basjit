from flask import render_template
from . import user_db
from models.product import Product
from models.category import Category

@user_db.route('/')
def home():
    # Fetch active featured products
    products = Product.query.filter(Product.status == 'active').order_by(Product.id.asc()).limit(6).all()
    if not products:
        products = Product.query.all()

    categories = Category.query.all()
    return render_template('user/page/home.html', product_list=products, categories=categories)
