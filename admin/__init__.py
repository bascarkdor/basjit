from flask import Blueprint

admin_db = Blueprint('admin', __name__)

# Force browsers to NEVER cache any admin pages
@admin_db.after_request
def disable_cache(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

from . import user
from . import product
from . import categories
from . import dashboard
from . import Auth