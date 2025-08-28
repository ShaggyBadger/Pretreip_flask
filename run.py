from dotenv import load_dotenv
load_dotenv()

import flask_app
from flask_app.blueprints import register_blueprints

if __name__ == "__main__":
    app = flask_app.app_constructor.app
    register_blueprints(app)
    app.run(
        debug=True, host="0.0.0.0", port=5000, use_reloader=True, use_debugger=False
    )