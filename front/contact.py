from flask import render_template, request, flash, redirect
from . import user_db

@user_db.route('/contact')
def contact():
    return render_template('user/page/contact.html')