from flask import Blueprint

user_db = Blueprint('user', __name__)

from . import about
from . import Auth
from . import cart
from . import checkout
from . import contact
from . import home
from . import payment_success
from . import product
from . import settings
from . import submit_order
