import flask_app.secretKey as secretKey
from pathlib import Path

SECRET_KEY = secretKey.SECRET_KEY

SQLALCHEMY_DATABASE_URI = None




'''
establish paths to various  directories for use in other parts of da program
'''

# root directory
BASE_DIR = Path(__file__).resolve().parent

# Main directories inside root
DATA_DIR = BASE_DIR / 'data'
DATABASE_DIR = DATA_DIR / 'database'

db_name = DATABASE_DIR / 'site_database.db'

