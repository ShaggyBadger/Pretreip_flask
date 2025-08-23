from os import EX_TEMPFAIL
from flask import render_template, request, jsonify, redirect, url_for, flash
from admin_app import admin_bp
from flask_app import settings
from flask_app.extensions import db
from flask_app.models.users import Users
from flask_app.models.tankgauge import TankCharts, TankData

# Import the refactored classes
from speedGauge_app.sgProcessor import Processor
from speedGauge_app.analytics import Analytics

@admin_bp.route('/')
def home():
    return render_template('admin/home.html')

@admin_bp.route('/upload_speedgauge', methods=['GET', 'POST'])
def upload_speedgauge():
    if request.method == 'GET':
        return render_template("admin/speedgauge/upload_speedgauge.html")

    if request.method == 'POST':
        file = request.files.get("file")
        if not file or file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        destination = settings.UNPROCESSED_SPEEDGAUGE_PATH / file.filename
        file.save(destination)

        try:
            # 1. Create instances of the refactored classes (no args needed)
            processor_obj = Processor()
            analytics_obj = Analytics()

            # 2. Run the standard flows. They will use the shared db.session.
            processor_obj.standard_flow()
            analytics_obj.standard_flow()

            return jsonify({"message": "File uploaded and processed successfully!"})

        except Exception as e:
            db.session.rollback()
            print(f"An error occurred during file processing: {e}")
            # It's good practice to log the full error
            import traceback
            traceback.print_exc()
            return jsonify({"error": "An internal error occurred during processing."}), 500

@admin_bp.route('/upload_success')
def upload_success():
    return render_template('admin/speedgauge/upload_success.html')

@admin_bp.route('/manage_users', methods=['GET', 'POST'])
def manage_users():
    query = Users.query

    # if method is POST, we will want one of several templates. We can figure
    # that out in here
    if request.method == 'POST':
        filters = request.form
        if filters.get('first_name'):
            query = query.filter(Users.first_name.ilike(f"%{filters['first_name']}%"))
        if filters.get('last_name'):
            query = query.filter(Users.last_name.ilike(f"%{filters['last_name']}%"))
        if filters.get('driver_id'):
            query = query.filter(Users.driver_id.ilike(f"%{filters['driver_id']}%"))
        if filters.get('dot_number'):
            query = query.filter(Users.dot_number.ilike(f"%{filters['dot_number']}%"))
        if filters.get('role'):
            query = query.filter(Users.role.ilike(f"%{filters['role']}%"))
        
        try:
            users = query.all()
        except Exception as e:
            users = []

    # if method is GET, then we want the basic query page to locate users
    else:
        try:
            users = query.limit(40).all()
        except Exception as e:
            users = []

    return render_template('admin/users/manage_users.html', users=users)

@admin_bp.route('/user/edit_user', methods=['POST'])
def edit_user():
    user_id = request.form.get("user_id")  # or request.json.get("user_id")
    user = Users.query.get_or_404(user_id)

    return render_template('admin/users/edit_user_form.html', user=user)

@admin_bp.route('/user/update_user', methods=['POST'])
def update_user():
    user_id = request.form.get("user_id")
    if not user_id:
        flash("No user ID provided.", "error")
        return redirect(url_for("admin.manage_users"))

    user = Users.query.get_or_404(user_id)

    # Update user fields from form data
    user.username = request.form.get('username')
    user.first_name = request.form.get('first_name')
    user.last_name = request.form.get('last_name')
    user.driver_id = request.form.get('driver_id')
    user.dot_number = request.form.get('dot_number')
    try:
        user.admin_level = int(request.form.get('admin_level', 0))
    except (TypeError, ValueError):
        user.admin_level = 0
    user.role = request.form.get('role')

    try:
        db.session.commit()
        flash("User updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        print(f"Error updating user {user_id}: {e}")
        flash("Error updating user.", "error")

    # If request is AJAX, return the fragment for injection.
    # Otherwise, fall back to redirecting to the full manage users page.
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        # Return the same fragment (form) - it will include flashed messages
        return render_template('admin/users/edit_user_form.html', user=user)
    else:
        return redirect(url_for("admin.manage_users"))

@admin_bp.route("/tanks/select", methods=["GET", "POST"])
def select_tank():
    if request.method == "POST":
        choice = request.form.get("action")
        if choice == "new":
            return redirect(url_for("admin.edit_tank", tank_id=None))
        elif choice == "edit":
            tank_id = request.form.get("tank_id")
            return redirect(url_for("admin.edit_tank", tank_id=tank_id))
    
    # GET: show selection page
    existing_tanks = TankData.query.all()
    return render_template("admin/tankcharts/select.html", charts=existing_tanks)

@admin_bp.route("/tanks/edit", methods=["GET", "POST"])
def edit_tank():
    chart_id = request.args.get("chart_id")  # comes from the redirect

    if request.method == "POST":
        # handle form submission for creating/updating a tank chart
        # get values from request.form
        # save to db
        tank = TankCharts.query.get(chart_id)
        chart = tank.tank_charts
        stores = tank.mapped_stores

        print(chart)
        print('\n************\n\n')
        print(stores)

        if not chart:
            flash("chart not found.", "error")
            return redirect(url_for('admin.select_tank'))

    return render_template("admin/tanks/edit.html", chart=chart, tank=tank, stores=stores)

