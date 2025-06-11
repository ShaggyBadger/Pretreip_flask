from flask import Flask
from flask_app.settings import SECRET_KEY, SQLALCHEMY_DATABASE_URI
from speedGauge.sg_inter import Controller as Controller
from flask_app import models

app = Flask(__name__)
sg_inter = Controller()
app.sg_inter = sg_inter

db_model = models.Utils()
app.db_model = db_model

app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# gotta import routes. idk why, you just do. 
import flask_app.routes
