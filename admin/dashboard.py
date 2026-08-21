from flask import render_template
from . import admin_db
from flask_login import login_required

@admin_db.route("/dashboard")
@login_required
def dashboard():
    return render_template('admin/page/dashboard.html')