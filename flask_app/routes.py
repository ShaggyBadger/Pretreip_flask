from flask import render_template, request, redirect, url_for, session, current_app
from flask_app.app_constructor import app
from flask_app.models.users import Users
from flask_app import models
from flask_app import settings
from datetime import timedelta
from datetime import datetime
from flask_app.extensions import db # Import db

app.permanent_session_lifetime = timedelta(days=7)


@app.before_request
def refresh_session():
    """
    set this to True if you want to allow users to remain signed in for 7 days
    """
    session.permanent = True


@app.route("/")
def home():
    if "user_id" in session:
        user = Users.query.filter_by(id=session['user_id']).first()
        print(user.admin_level)
        print(user.role)
        if user.admin_level < 1 and user.role == 'swto':
            return render_template("dashboard-swto.html")
        elif user.admin_level >= 1:
            return render_template('dashboard-admin.html')
        else:
            return render_template('dashboard-standard.html')
        
    return render_template("home_guest.html")

@app.route("/tempUpload", methods=["GET", "POST"])
def tempUpload():
    if request.method == "POST":
        file = request.files.get("file")
        destination = settings.UNPROCESSED_SPEEDGAUGE_PATH / file.filename
        file.save(destination)


    return render_template("tempUpload.html")
