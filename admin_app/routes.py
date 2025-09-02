from logging import raiseExceptions
from os import EX_TEMPFAIL
import json
from flask import render_template, request, jsonify, redirect, url_for, flash, abort
from admin_app import admin_bp
from flask_app import settings
from flask_app.extensions import db
from flask_app.models.users import Users
from flask_app.models.tankgauge import StoreData, TankCharts, TankData, StoreTankMap

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
    query = TankData.query
    query = query.order_by(TankData.name.asc())
    existing_tanks = query.all()
    return render_template("admin/tanks/select.html", tanks=existing_tanks)

@admin_bp.route("/tanks/edit", methods=["GET", "POST"])
def edit_tank():
    if request.method == "POST":
        tank_id = request.form.get("tank_id")  # comes from the redirect
        # handle form submission for creating/updating a tank chart
        # get values from request.form
        query = TankData.query
        query = query.filter_by(id=tank_id)
        tank = query.first()
        charts = tank.tank_charts

        # I'll keep stores in here for now, but I'll comment it out bc I don't actually need it
        #stores = tank.mapped_stores


        if not charts:
            flash("chart not found.", "error")
            return redirect(url_for('admin.select_tank'))

        return render_template("admin/tanks/edit.html", charts=charts, tank=tank)
    else:
        abort(404)

@admin_bp.route('/tanks/edit-submit', methods=["POST"])
def edit_tankChart_success():
    if request.method == "POST":
        row_ids = request.form.getlist("row_id")
        inches_list = request.form.getlist("inches")
        gallons_list = request.form.getlist("gallons")
        misc_list = request.form.getlist("misc_info")
        tank_id = request.form.get('tank_id')

        try:
            for rid, inch, gal, misc in zip(row_ids, inches_list, gallons_list, misc_list):
                row = TankCharts.query.get(rid)
                if row:
                    row.inches = inch
                    row.gallons = gal
                    row.misc_info = misc

            db.session.commit()

        except Exception:
            db.session.rollback()
            flash("Failed to update tank charts.", "error")

        
        query = TankData.query
        query = query.filter_by(id=tank_id)
        tank = query.first()
        charts = tank.tank_charts

        return render_template("admin/tanks/edit-success.html", tank=tank, charts=charts)

    else:
        abort(404)

@admin_bp.route('/tanks/edit-tankdata', methods=["POST"])
def edit_tankdata_submit():
    # process main tank info here
    if request.method == "POST":
        tank_id = request.form.get('tank_id')

        # Remove csrf_token and tank_id if you don't want to update them
        ignore_keys = ['csrf_token', 'tank_id']

        try:
            # get the tank obj from the database
            tank = TankData.query.get(tank_id)

            # update the columns
            tank.name = request.form.get('name', tank.name)
            tank.manufacturer = request.form.get('manufacturer', tank.manufacturer)
            tank.model = request.form.get('model', tank.model)
            tank.capacity = int(request.form.get('capacity', tank.capacity))
            tank.max_depth = int(request.form.get('max_depth', tank.max_depth))
            tank.misc_info = request.form.get('misc_info', tank.misc_info)
            tank.chart_source = request.form.get('chart_source', tank.chart_source)
            tank.description = request.form.get('description', tank.description)

            db.session.commit()
        
        except Exception:
            db.session.rollback()
            flash("Failed to update tank charts.", "error")
        
        tank = TankData.query.get(tank_id)

        return render_template('admin/tanks/submit-tankData-update.html', tank=tank)
    else:
        abort(404)

@admin_bp.route('/stores/select.html')
def select_store():
    # build the query. order by:
    # 1: store_type (exxon, speedway, etc)
    # 2: city
    # 3: store_num
    query = StoreData.query
    query = query.order_by(
        StoreData.store_type.asc(),
        StoreData.city.asc(),
        StoreData.store_num.asc()
        )
    stores = query.all()
    
    return render_template('admin/stores/select.html', stores=stores)

@admin_bp.route('/stores/edit-store.html', methods=["POST", "GET"])
def edit_store():
    store_id = request.form.get('store_id') or request.args.get("store_id")
    try:
        store_id = int(store_id)   # convert to integer
    except ValueError:
        return "Invalid store_id", 400

    query = StoreData.query
    query = query.filter_by(id = store_id)
    store = query.first()

    mapped_rows = (
        db.session.query(StoreTankMap, TankData)
        .join(TankData, StoreTankMap.tank_id == TankData.id)
        .filter(StoreTankMap.store_id == store.id)
        .all()
        )
    
    store_tanks = store.store_tanks_map
    tanks = []

    for tank in store_tanks:
        fuel_type = tank.fuel_type
        tank_id = tank.tank_id

        query = TankData.query
        query = query.filter_by(id=tank_id)
        tank_obj = query.first()
        tank_dict = {
            'fuel_type': fuel_type,
            'tank_id': tank_obj.id,
            'name': tank_obj.name,
            'manufacturer': tank_obj.manufacturer,
            'model': tank_obj.model,
            'capacity': tank_obj.capacity,
            'max_depth': tank_obj.max_depth,
            'misc_info': tank_obj.misc_info,
            'chart_source': tank_obj.chart_source,
            'description': tank_obj.description
        }
        tanks.append(tank_dict)

    return render_template('/admin/stores/edit-store.html', store=store, tanks_list=tanks)

@admin_bp.route('/stores/submit-edits.html', methods=["POST"])
def submit_store_edit():
    store_id = request.form.get('store_id')
    store = StoreData.query.get_or_404(store_id)
    form = request.form

    # Capture "before" state
    before_data = {col.name: getattr(store, col.name) for col in StoreData.__table__.columns}

    try:
        # Update store fields (skip id)
        for column in StoreData.__table__.columns:
            if column.name == 'id':
                continue
            if column.name in form:
                value = form.get(column.name)
                if value == '':
                    value = None
                setattr(store, column.name, value)
        

        # Parse tanks JSON safely
        tanks_dict = json.loads(form.get('tanks_json', '[]'))

        # Delete old mappings in one shot
        StoreTankMap.query.filter_by(store_id=store.id).delete(synchronize_session=False)

        # Insert new mappings
        for tank in tanks_dict:
            new_map = StoreTankMap(
                store_id=store.id,
                tank_id=tank.get('tank_id'),
                fuel_type=tank.get('fuel_type')
            )
            db.session.add(new_map)

        # Commit all at once
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        raise

    # Capture "after" state
    after_data = {col.name: getattr(store, col.name) for col in StoreData.__table__.columns}

    return render_template(
        'admin/stores/submit-edits.html',
        before=before_data,
        after=after_data,
        store_id=store_id
    )

@admin_bp.route('/api/get_tanks')
def get_tanks():
    tank_list = []
    fuel_type_list = []

    query = TankData.query
    query = query.order_by(
        TankData.max_depth.asc(),
        TankData.capacity.asc()
        )
    tanks = query.all()
    
    for tank in tanks:
        tank_dict = {
            'id': tank.id,
            'name': tank.name,
            'capacity': tank.capacity,
            'max_depth': tank.max_depth,
            'misc_info': tank.misc_info,
            'description': tank.description
        }

        tank_list.append(tank_dict)
    
    query = StoreTankMap.query  # start with the base query
    query = query.with_entities(StoreTankMap.fuel_type)  # select only the fuel_type column
    query = query.distinct()  # get only distinct values
    fuel_types = query.all()  # execute the query

    for i in fuel_types:
        fuel_type = i[0]
        fuel_type_list.append(fuel_type)

    response_object = {
        'tank_list': tank_list,
        'fuel_type_list': fuel_type_list
    }

    return jsonify(response_object)

@admin_bp.route('/create-store', methods=["POST"])
def create_store():
    new_store_row = StoreData()
    db.session.add(new_store_row)
    db.session.commit()

    # now redirect to edit page with the store_id
    return redirect(url_for("admin.edit_store", store_id=new_store_row.id))
