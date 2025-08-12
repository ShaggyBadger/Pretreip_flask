import os
from pathlib import Path

SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")

# A list of DOT numbers that are granted the 'premium' role upon registration
AUTHORIZED_DOT_NUMBERS = ['943113']

"""
establish paths to various  directories for use in other parts of da program
"""
# root directory
BASE_DIR = Path(__file__).resolve().parent

# Main directories inside root
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = DATA_DIR / "database"

# speedgauge directory paths
SPEEDGAUGE_DIR = DATA_DIR / "speedGauge_files"
PROCESSED_SPEEDGAUGE_PATH = SPEEDGAUGE_DIR / "processed"
UNPROCESSED_SPEEDGAUGE_PATH = SPEEDGAUGE_DIR / "unprocessed"

speedGuage_data_tbl_name = "speedGauge_data"