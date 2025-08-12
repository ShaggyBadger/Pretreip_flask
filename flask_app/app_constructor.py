import os
import urllib.parse
from flask import Flask
from datetime import timedelta
from flask_app.settings import SECRET_KEY, AUTHORIZED_DOT_NUMBERS
#from tankGauge_app import tankGauge_bp
#from speedGauge_app import speedGauge_bp
from admin_app import admin_bp
from auth_app import auth_bp
from flask_app.extensions import db, migrate

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["AUTHORIZED_DOT_NUMBERS"] = AUTHORIZED_DOT_NUMBERS
    app.permanent_session_lifetime = timedelta(days=7)

    # Configure the database
    MYSQL_HOST = os.environ.get("MYSQL_HOST")
    MYSQL_USER = os.environ.get("MYSQL_USER")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
    MYSQL_DB = os.environ.get("MYSQL_DB")
    
    # URL-encode the password to handle special characters
    encoded_password = urllib.parse.quote_plus(MYSQL_PASSWORD)
    db_uri = f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}/{MYSQL_DB}?charset=utf8mb4"
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}/{MYSQL_DB}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = True
    print(f"DEBUG: SQLALCHEMY_DATABASE_URI = {db_uri}")

    

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Explicitly import Users model and access its table to force mapping
    from flask_app.models.users import Users
    _ = Users.__table__

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(tankGauge_bp, url_prefix='/tankgauge')
    app.register_blueprint(speedGauge_bp, url_prefix='/speedgauge')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app

# Create the Flask app instance for global use
app = create_app()

# Import routes after the app is created to avoid circular imports
import flask_app.routes
