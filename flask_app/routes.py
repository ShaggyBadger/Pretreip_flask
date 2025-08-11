from flask import render_template, request, redirect, url_for, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_app.app_constructor import app
from flask_app import models
from flask_app import settings
from datetime import timedelta
from datetime import datetime
import speedGauge_app as sga

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
        return render_template("dashboard.html")
    return render_template("home_guest.html")


@app.route("/failed_login")
def failed_login():
    return render_template("failed_login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        utils_obj = models.Utils()
        user = utils_obj.check_password(username, password)

        if user:
            session["user_id"] = user["id"]
            session['admin_level'] = user.get('admin_level', 0)
            session["username"] = username
            url = url_for("home")

            return redirect(url)

        else:
            url = url_for("failed_login")

            return redirect(url)

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        utils_obj = models.Utils()
        #user_id = utils_obj.register_user(username, password)
        user_id = 1

        # register_user method returns True if user already exists in db
        print(f"\n\n*****\n{utils_obj.user_exists}\n*****\n\n")
        if utils_obj.user_exists is True:
            url = url_for("failed_register")

            return redirect(url)

        # register_user method returns
        else:
            session["user_id"] = user_id
            session["username"] = username
            url = url_for("home")

            return redirect(url)
        
    return render_template("register.html")


@app.route("/failed_register")
def failed_register():
    return render_template("failed_register.html")


@app.route("/logout")
def logout():
    session.clear()  # This clears all session data
    return redirect(url_for("home"))


@app.route("/tempUpload", methods=["GET", "POST"])
def tempUpload():
    if request.method == "POST":
        file = request.files.get("file")
        destination = settings.UNPROCESSED_SPEEDGAUGE_PATH / file.filename
        file.save(destination)
    return render_template("tempUpload.html")


@app.route("/speedgauge", methods=["GET", "POST"])
def speedGauge():
    if "user_id" not in session:
        return redirect(url_for("home"))

    user_id = session["user_id"]
    db_model = current_app.db_model
    driver_id = db_model.retrieve_driver_id(user_id)

    sg_api = sga.SpeedgaugeApi.Api(driver_id, db_model)
    sg_data = sg_api.build_speedgauge_report()

    # build list of dates
    available_dates = [entry["start_date"] for entry in sg_data]

    # store user-requested date
    selected_date_str = request.args.get("start_date")

    # Convert to datetime if selected, otherwise use most recent
    if selected_date_str:
        try:
            selected_date = datetime.fromisoformat(selected_date_str)
        except ValueError:
            selected_date = available_dates[0]
    else:
        selected_date = available_dates[0]

    # Match data by date (use .date() to ignore time)
    selected_data = next(
        (
            entry
            for entry in sg_data
            if entry["start_date"].date() == selected_date.date()
        ),
        None,
    )

    # collect analytic data
    driver_analytics = sg_api.get_driver_analytics(driver_id, selected_date)
    company_analytics = sg_api.get_company_analytics(selected_date)

    return render_template(
        "speedgauge.html",
        available_dates=available_dates,
        selected_date=selected_date,
        selected_data=selected_data,
        driver_analytics=driver_analytics,
        company_analytics=company_analytics
    )
