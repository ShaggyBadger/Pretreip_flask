from flask import Flask, request, session, g
from flask_app.settings import SECRET_KEY
from dbConnector import fetch_session # Import the generic session provider
from flask_app import models
from tankGauge_app import tankGauge_bp

# flask_app/app_constructor.py
def create_app():
    app = Flask(__name__)
    # ... app configuration ...

    # This function runs BEFORE each request
    @app.before_request
    def before_request_hook():
        # Get a session from the generator and store it in g
        # 'next(get_db())' gets the actual session object from the generator
        g.db_session = next(get_db())

    # This function runs AFTER each request (even if errors occur)
    @app.teardown_appcontext
    def teardown_db_session(exception=None):
        # Retrieve the session from g (and remove it from g)
        db = g.pop('db_session', None)
        if db is not None:
            db.close() # Close the session to release the connection

    # ... register blueprints, etc. ...
    return app

app = Flask(__name__)
# register blueprints
app.register_blueprint(tankGauge_bp)

db_model = models.Utils()
app.db_model = db_model

app.config["SECRET_KEY"] = SECRET_KEY





# gotta import routes. idk why, you just do.
import flask_app.routes