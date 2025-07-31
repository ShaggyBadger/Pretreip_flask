from flask import Flask, g, session
from datetime import timedelta
from flask_app.settings import SECRET_KEY
from dbConnector import fetch_session, init_db
from flask_app import models
from tankGauge_app import tankGauge_bp

# Initialize the database
init_db()

# Make a function to create the app
def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.permanent_session_lifetime = timedelta(days=7)

    # Register blueprints
    app.register_blueprint(tankGauge_bp, url_prefix='/tankgauge')

    # Attach a database utility to the app context
    app.db_model = models.Utils()

    @app.before_request
    def before_request_hook():
        # Set session to permanent
        session.permanent = True
        # Get a database session from the pool and store it in the application context
        g.db_session = next(fetch_session())

    @app.teardown_appcontext
    def teardown_db_session(exception=None):
        # Pop the session from the application context and close it
        db_session = g.pop('db_session', None)
        if db_session is not None:
            db_session.close()

    return app

# Create the Flask app instance for global use
app = create_app()

# Import routes after the app is created to avoid circular imports
import flask_app.routes