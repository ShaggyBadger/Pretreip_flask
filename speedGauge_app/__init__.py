from flask import Blueprint

speedGauge_bp = Blueprint(
    'speedGauge_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/speedGauge_app/static' # To avoid conflict with other blueprints
)

from . import routes, SpeedgaugeApi, DbAudit, sgProcessor, dbManagement