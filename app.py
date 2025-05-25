from flask import Flask
#from models import db
from settings import SECRET_KEY, SQLALCHEMY_DATABASE_URI

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#db.init_app(app)

# You can import routes after app is defined
import routes
