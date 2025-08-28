from flask import Blueprint

tankGauge_bp = Blueprint(
    'tankgauge', __name__,
    template_folder='templates',
    static_folder='static',
)

from . import routes

