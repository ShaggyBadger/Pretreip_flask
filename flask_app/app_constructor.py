import os
import urllib.parse
from flask import Flask
from datetime import timedelta
from flask_app.settings import SECRET_KEY, AUTHORIZED_DOT_NUMBERS
from flask_app.extensions import db, migrate
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from markupsafe import Markup

# make tracebacks more better
from rich.traceback import install
from flask import got_request_exception
from rich.console import Console
from rich.traceback import Traceback

console = Console()
install(show_locals=False)

def nl2br(value):
    return Markup(value).replace('\n', '<br>\n')

def create_app():
    app = Flask(__name__)
    app.jinja_env.filters['nl2br'] = nl2br
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["AUTHORIZED_DOT_NUMBERS"] = AUTHORIZED_DOT_NUMBERS
    app.config['WTF_CSRF_TRUSTED_ORIGINS'] = [
    'https://thejoshproject.xyz',
    'https://www.thejoshproject.xyz'
]
    app.permanent_session_lifetime = timedelta(days=7)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
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

    # set this to True if I feel like seeing all the sql statemnets that sqlalchemy makes
    app.config['SQLALCHEMY_ECHO'] = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Explicitly import Users model and access its table to force mapping
    from flask_app.models.users import Users
    _ = Users.__table__

    from flask_app.blueprints import register_blueprints
    register_blueprints(app)

    return app

# Create the Flask app instance for global use
app = create_app()

# make tracebacks beuatiful again
def log_exception(sender, exception, **extra):
    tb = Traceback.from_exception(
        type(exception), exception, exception.__traceback__, show_locals=False
    )
    console.print(tb)

# Connect Rich to Flask route exceptions
got_request_exception.connect(log_exception, app)

# Import routes after the app is created to avoid circular imports
import flask_app.routes