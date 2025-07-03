from flask import Flask
from flask_app.settings import SECRET_KEY
from flask_app import models

app = Flask(__name__)

db_model = models.Utils()
app.db_model = db_model

app.config['SECRET_KEY'] = SECRET_KEY

# gotta import routes. idk why, you just do. 
import flask_app.routes
