from flask import render_template
from . import user_db

@user_db.route('/about')
def about():
    return render_template('user/page/about.html')