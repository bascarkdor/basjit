from flask import render_template
from . import admin_db
from flask_login import login_required

@admin_db.route('/categories')
@login_required
def categories():
    return render_template('admin/page/category.html')