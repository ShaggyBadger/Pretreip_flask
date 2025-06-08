#from flask_app.app import app
import flask_app

if __name__ == "__main__":
	app = flask_app.app_constructor.app
	app.run(debug=True, use_reloader=False,
	use_debugger=False)
