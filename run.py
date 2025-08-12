from dotenv import load_dotenv
load_dotenv()

import flask_app

if __name__ == "__main__":
    app = flask_app.app_constructor.app
    app.run(
        debug=True, host="0.0.0.0", port=5000, use_reloader=True, use_debugger=False
    )
