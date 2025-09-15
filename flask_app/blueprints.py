from tankGauge_app import tankGauge_bp
from speedGauge_app import speedGauge_bp
from admin_app import admin_bp
from auth_app import auth_bp
from pretrip_app import pretrip_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(tankGauge_bp, url_prefix='/tankgauge')
    app.register_blueprint(speedGauge_bp, url_prefix='/speedgauge')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(pretrip_bp, url_prefix='/pretrip')
