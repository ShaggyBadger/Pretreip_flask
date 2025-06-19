import os
from pathlib import Path

SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
if SECRET_KEY is None:
  import flask_app.secretKey as secretKey
  SECRET_KEY = secretKey.SECRET_KEY
print(SECRET_KEY)

SQLALCHEMY_DATABASE_URI = None

'''
establish paths to various  directories for use in other parts of da program
'''

# root directory
BASE_DIR = Path(__file__).resolve().parent

# Main directories inside root
DATA_DIR = BASE_DIR / 'data'
DATABASE_DIR = DATA_DIR / 'database'

# speedgauge directory paths
SPEEDGAUGE_DIR = DATA_DIR / 'speedGauge_files'
PROCESSED_SPEEDGAUGE_PATH = SPEEDGAUGE_DIR / 'processed'
UNPROCESSED_SPEEDGAUGE_PATH = SPEEDGAUGE_DIR / 'unprocessed'

db_name = DATABASE_DIR / 'site_database.db'
speedGuage_data_tbl_name = 'speedGauge_data'
