import os
import urllib.parse
from flask import Flask
from datetime import timedelta
from flask_app.settings import SECRET_KEY, AUTHORIZED_DOT_NUMBERS
from flask_app.extensions import db, migrate
from flask_wtf.csrf import CSRFProtect

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["AUTHORIZED_DOT_NUMBERS"] = AUTHORIZED_DOT_NUMBERS
    app.permanent_session_lifetime = timedelta(days=7)
    csrf = CSRFProtect(app)

    # Configure the database
    DB_MODE = os.environ.get("DB_MODE", "prod")  # Default to production

    if DB_MODE == "tunnel":
        # Configuration for SSH Tunnel
        MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
        MYSQL_PORT = os.environ.get("MYSQL_PORT", "3307")
    else:
        # Production configuration
        MYSQL_HOST = os.environ.get("MYSQL_HOST")
        MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")

    MYSQL_USER = os.environ.get("MYSQL_USER")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
    MYSQL_DB = os.environ.get("MYSQL_DB")

    # URL-encode the password to handle special characters
    if MYSQL_PASSWORD:
        encoded_password = urllib.parse.quote_plus(MYSQL_PASSWORD)
        db_uri = f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
    else:
        # Handle case where password might be empty (not recommended for prod)
        db_uri = f"mysql+pymysql://{MYSQL_USER}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = True

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Explicitly import Users model and access its table to force mapping
    from flask_app.models.users import Users
    _ = Users.__table__

    return app

# Create the Flask app instance for global use
app = create_app()

# Import routes after the app is created to avoid circular imports
import flask_app.routes