from flask import Flask, request
from flask_app.settings import SECRET_KEY
from flask_app import models
import datetime

app = Flask(__name__)

db_model = models.Utils()
app.db_model = db_model

app.config["SECRET_KEY"] = SECRET_KEY

@app.before_request
def log_request():
    # Get details from the request
    ip_address = request.remote_addr
    path = request.path
    method = request.method
    user_agent = request.headers.get('User-Agent', '')

    # get out of here if the path is lame
    if path.startswith('/static') or path.endswith('.ico'):
        return


    # Insert into DB
    query = """
        INSERT INTO visit_log_table (ip_address, path, method, user_agent)
        VALUES (%s, %s, %s, %s)
    """
    values = (ip_address, path, method, user_agent)
    
    try:
        conn = app.db_model.get_db_connection()
        c = conn.cursor()
        c.execute(query, values)
        conn.commit()
    except Exception as e:
        pass
    finally:
        c.close()
        conn.close()

# gotta import routes. idk why, you just do.
import flask_app.routes
