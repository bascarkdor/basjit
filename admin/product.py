from flask import render_template
from . import admin_db
from flask_login import login_required

@admin_db.route('/product')
@login_required
def product():
    return render_template('admin/page/product.html')