from rich.traceback import install
install()
from flask_app import settings
from flask_app import app_constructor
from flask_app import models
from flask_app import routes

__version__ = 0.1
__author__ = "The Bulk Fuel Ranger"
