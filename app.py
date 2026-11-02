import os
import sys

# Ensure current project directory is on Python search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, flash, request, redirect, url_for
from flask_login import LoginManager

from config import Config
from extensions import db, migrate, limiter, csrf, cors
import admin
from front import user_db
from models.user import User

app = Flask(__name__)

# Load database settings from config.py
app.config.from_object(Config)

# Attach extensions to Flask app
db.init_app(app)
migrate.init_app(app, db)  # <-- This adds the 'flask db' command
limiter.init_app(app)
csrf.init_app(app)
cors.init_app(app)

# Register custom error page handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html'), 404

@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template('error/429.html', error=e.description), 429

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error/500.html'), 500

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
# Redirect unauthenticated users trying to access protected routes
login_manager.login_view = 'user.login'

@login_manager.unauthorized_handler
def unauthorized_callback():
    if request.path.startswith('/admin'):
        flash('Please login to access the admin portal.', 'warning')
        return redirect(url_for('admin.login', next=request.url))
    flash('Please log in or register to complete your order.', 'warning')
    return redirect(url_for('user.login', next=request.url))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(admin.admin_db, url_prefix='/admin')

app.register_blueprint(user_db, url_prefix='/')

# --- API Test Endpoint for CORS Testing ---
@app.route('/api/test', methods=['GET'])
def api_test():
    return {
        "status": "success",
        "message": "CORS is working! Angular connected successfully to Flask backend on port 9000."
    }

# --- CLI Commands ---
@app.cli.command('seeddb')
def seeddb_command():
    """Seed admin user, categories, and products."""
    from seeddb import seed_database
    seed_database()

if __name__ == '__main__':
    app.run(debug=True)