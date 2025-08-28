from flask_app.app_constructor import app
from flask_app.blueprints import register_blueprints

register_blueprints(app)

if __name__ == "__main__":
    app.run()