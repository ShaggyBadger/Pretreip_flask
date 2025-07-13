from flask import Flask, request, session
from flask_app.settings import SECRET_KEY
from flask_app import models
import datetime

app = Flask(__name__)

db_model = models.Utils()
app.db_model = db_model

app.config["SECRET_KEY"] = SECRET_KEY

@app.after_request
def log_request(response):
    ip_address = request.remote_addr
    path = request.path
    method = request.method
    user_agent = request.headers.get('User-Agent', '')
    username = session.get('username', 'anonymous')
    status_code = response.status_code

    # Skip static files and favicon
    if path.startswith('/static') or path.endswith('.ico'):
        return response

    query = """
        INSERT INTO visit_log_table (ip_address, path, method, user_agent, username, status_code)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = (ip_address, path, method, user_agent, username, status_code)

    try:
        conn = app.db_model.get_db_connection()
        c = conn.cursor()
        c.execute(query, values)
        conn.commit()
    except Exception as e:
        # Optional: log this failure somewhere else
        pass
    finally:
        c.close()
        conn.close()

    return response  # Must return the response!

# gotta import routes. idk why, you just do.
import flask_app.routes
