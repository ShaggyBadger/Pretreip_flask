from rich.traceback import install
install()
from flask import Flask
#from models import db
import os
from flask import Flask
from dotenv import load_dotenv # Keep this for your laptop development!
from settings import SECRET_KEY, SQLALCHEMY_DATABASE_URI

# --- Load Environment Variables for Laptop Development ---
# This will try to load variables from a .env file (if it exists)
# It effectively does nothing if there's no .env file or if running on Pythonista
# where .env files aren't typically used.
load_dotenv()

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Determine SECRET_KEY Source ---
secret_key_value = None # Initialize to None

# 1. Attempt to get SECRET_KEY from environment variable (highest priority)
secret_key_value = os.environ.get('SECRET_KEY')

if secret_key_value:
  app.config['SECRET_KEY'] = secret_key_value
  print("SECRET_KEY loaded from environment variable.")
else:
  # 2. If not found in environment, try to load from secretKey.py (fallback for Pythonista/dev)
  try:
    import secretKey # Assumes secretKey.py is in the same directory or importable path
    app.config['SECRET_KEY'] = secretKey.SECRET_KEY
    print("SECRET_KEY loaded from secretKey.py (environment variable not found).")
  except ImportError:
    # 3. If neither is found, raise a critical error
    raise RuntimeError(
      "SECRET_KEY is not set! "
      "Please set it as an environment variable (e.g., in .env or via hosting platform) "
      "OR ensure secretKey.py exists and is importable with a SECRET_KEY variable defined."
      )


app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#db.init_app(app)

# You can import routes after app is defined
import routes
