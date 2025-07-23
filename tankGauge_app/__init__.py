from flask import Blueprint

tankGauge_bp = Blueprint(
    'tankgauge', __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/tankgauge'
)

from tankGauge_app import routes
from . import models