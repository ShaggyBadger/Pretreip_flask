from flask import render_template, request, redirect, url_for, session
from datetime import datetime
from . import speedGauge_bp
from flask_app import utils
from . import SpeedgaugeApi

@speedGauge_bp.route("/", methods=["GET", "POST"])
def speedGauge():
    if "user_id" not in session:
        # TODO: In the next phase, this should redirect to the auth blueprint's login page
        return redirect(url_for("home"))

    user_id = session["user_id"]
    utils_obj = utils.Utils() 
    driver_id = utils_obj.retrieve_driver_id(user_id)

    sg_api = SpeedgaugeApi.Api(driver_id)
    sg_data = sg_api.build_speedgauge_report()

    # build list of dates
    if sg_data:
        available_dates = [entry["start_date"] for entry in sg_data]
    else:
        available_dates = []

    # store user-requested date
    selected_date_str = request.args.get("start_date")

    # Convert to datetime if selected, otherwise use most recent
    if selected_date_str:
        try:
            selected_date = datetime.fromisoformat(selected_date_str)
        except ValueError:
            selected_date = available_dates[0] if available_dates else None
    else:
        selected_date = available_dates[0] if available_dates else None

    # Match data by date (use .date() to ignore time)
    selected_data = None
    if selected_date and sg_data:
        selected_data = next(
            (
                entry
                for entry in sg_data
                if entry["start_date"].date() == selected_date.date()
            ),
            None,
        )

    # collect analytic data
    driver_analytics = None
    company_analytics = None
    if driver_id and selected_date:
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