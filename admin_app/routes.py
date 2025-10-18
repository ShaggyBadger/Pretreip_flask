from logging import raiseExceptions
from os import EX_TEMPFAIL
import json
import pandas as pd
from pathlib import Path
from flask import render_template, request, jsonify, redirect, url_for, flash, abort
from admin_app import admin_bp
from flask_app import settings
from flask_app.extensions import db
from flask_app.models.users import Users
from flask_app.models.tankgauge import StoreData, TankCharts, TankData, StoreTankMap

# Import the refactored classes
from speedGauge_app.sgProcessor import Processor
from speedGauge_app.analytics import Analytics
# Import the pretrip validation utility
from .pretrip.utils import validate_csv_headers

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

@admin_bp.route('/user/display_edit_user_form', methods=['POST'])
def display_edit_user_form():
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
    user.admin_level = int(request.form.get('admin_level', 0))
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

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = Users.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.role = request.form.get('role')
        user.admin_level = int(request.form.get('admin_level', 0))

        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin_bp.manage_users'))
    return render_template('admin/edit_user_form.html', user=user)

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
            return redirect(url_for("admin.create_tank"))
        elif choice == "edit":
            tank_id = request.form.get("tank_id")
            return redirect(url_for("admin.edit_tank", tank_id=tank_id))
    
    # GET: show selection page
    query = TankData.query
    query = query.order_by(TankData.name.asc())
    existing_tanks = query.all()
    return render_template("admin/tanks/select.html", tanks=existing_tanks)

@admin_bp.route('/tanks/create', methods=['GET', 'POST'])
def create_tank():
    if request.method == 'POST':
        # Get form data, converting empty strings for integer fields to None
        capacity_str = request.form.get('capacity')
        max_depth_str = request.form.get('max_depth')

        try:
            capacity = int(capacity_str) if capacity_str else None
            max_depth = int(max_depth_str) if max_depth_str else None
        except (ValueError, TypeError):
            flash('Capacity and Max Depth must be numbers.', 'error')
            return redirect(url_for('admin.create_tank'))

        # Create a new TankData object from form data
        new_tank = TankData(
            name=request.form.get('name'),
            manufacturer=request.form.get('manufacturer'),
            model=request.form.get('model'),
            capacity=capacity,
            max_depth=max_depth,
            misc_info=request.form.get('misc_info'),
            chart_source=request.form.get('chart_source'),
            description=request.form.get('description')
        )
        db.session.add(new_tank)
        db.session.commit()

        # Process the uploaded CSV file
        file = request.files.get("csv_file")
        if not file or file.filename == '':
            flash('No CSV file provided', 'error')
            return redirect(url_for('admin.create_tank'))

        ext = Path(file.filename).suffix.lower()
        if ext == '.csv':
            df = pd.read_csv(file, encoding="utf-8")
        elif ext in ['.xls', '.xlsx']:
            df = pd.read_excel(file)
        else:
            flash('Unsupported file type. Please upload a CSV or Excel file.', 'error')
            return redirect(url_for('admin.create_tank'))

        df.columns = [col.lower() for col in df.columns]
        column_map = {"inches": "inch", "gallons": "gallon"}
        df.rename(columns=column_map, inplace=True)

        if "inch" not in df.columns or "gallon" not in df.columns:
            flash('CSV/Excel file must have \'inch\'/\'inches\' and \'gallon\'/\'gallons\' columns.', 'error')
            return redirect(url_for('admin.create_tank'))

        records = df[["inch", "gallon"]].to_dict(orient="records")
        
        for record in records:
            new_row = TankCharts(
                tank_type_id=new_tank.id,
                inches=record.get('inch'),
                gallons=record.get('gallon'),
                tank_name=new_tank.name
            )
            db.session.add(new_row)
        
        db.session.commit()

        # Update the TankData object with max_depth and capacity from the chart
        # if they were not provided in the form
        query = TankCharts.query.filter(TankCharts.tank_type_id == new_tank.id).order_by(TankCharts.inches.desc())
        chart = query.first()
        if chart:
            if not new_tank.capacity:
                new_tank.capacity = chart.gallons
            if not new_tank.max_depth:
                new_tank.max_depth = chart.inches
            db.session.commit()

        flash('Tank created successfully!', 'success')
        return redirect(url_for('admin.select_tank'))

    return render_template('admin/tanks/create_tank.html')

@admin_bp.route('/tanks/no-tank-charts-edit', methods=["GET"])
def no_tank_charts_edit():
    if request.method != "GET":
        abort(404)
    
    tank_id = request.args.get("tank_id", type=int)  # read from URL ?tank_id=42
    if not tank_id:
        abort(404)
    
    query = TankData.query
    query = query.filter(TankData.id == tank_id)
    tank = query.first()
    
    return render_template("admin/tanks/no-tank-charts-edit.html", tank=tank)

@admin_bp.route("/tanks/upload-tank-chart-csv", methods=["POST"])
def upload_tank_chart_csv():
    if request.method != "POST":
        abort(404)
    
    tank_id = request.form.get("tank_id", type=int)
    file = request.files.get("csv_file")

    if not tank_id and not file:
        abort(404)
    
    # Get the file extension
    ext = Path(file.filename).suffix.lower()  # gives '.csv' or '.xlsx'

    if ext == '.csv':
        df = pd.read_csv(file, encoding="utf-8")
    elif ext in ['.xls', '.xlsx']:
        df = pd.read_excel(file)
    else:
        return render_template(
            "admin/tanks/bad-file-type.html",
            error="Unsupported file type. Please upload a CSV or Excel file."
            )

    # Standardize column names
    df.columns = [col.lower() for col in df.columns]
    column_map = {
        "inches": "inch",
        "gallons": "gallon"
    }
    df.rename(columns=column_map, inplace=True)

    # Check if required columns are present
    if "inch" not in df.columns or "gallon" not in df.columns:
        return render_template(
            "admin/tanks/bad-file-type.html",
            error="CSV/Excel file must have 'inch'/'inches' and 'gallon'/'gallons' columns."
        )

    # records is a list of dictionaries
    # each dict has 2 keys: inch, gallon
    records = df[["inch", "gallon"]].to_dict(orient="records")
    
    #insert the data into the database
    tank = TankData.query.filter(TankData.id == tank_id).first()
    tank_name = tank.name

    for record in records:
        inches = record.get('inch')
        gallons = record.get('gallon')

        # check if this inch is already in the database for this tank
        existing = TankCharts.query.filter_by(
            tank_type_id=tank_id,
            inches=inches
            ).first()
        
        # if it is already in, then update the record with the gallons
        if existing:
            existing.gallons = gallons
        
        else:
            new_row = TankCharts(
                tank_type_id=tank_id,
                inches=inches,
                gallons=gallons,
                tank_name=tank_name
            )

            # add the row to database sesson
            db.session.add(new_row)
    
    db.session.commit()

    # update the TankData model for this tank for max depth and max inches
    query = TankCharts.query
    query = query.filter(TankCharts.tank_type_id == tank_id)
    query = query.order_by(TankCharts.inches.desc())
    chart = query.first()

    tank.capacity = chart.gallons
    tank.max_depth = chart.inches
    db.session.commit()

    # gather some data to send to the template
    charts = TankCharts.query.filter_by(tank_type_id=tank.id).order_by(TankCharts.inches).all()

    # render the template!
    return render_template("admin/tanks/upload-tank-chart-csv.html", tank=tank, chart=charts)

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
            return redirect(url_for('admin.no_tank_charts_edit', tank_id=tank.id))

        return render_template("admin/tanks/edit.html", charts=charts, tank=tank)
    
    if request.method == "GET":
        tank_id = request.args.get("tank_id")
        if not tank_id:
            abort(404)
        
        query = TankData.query
        query = query.filter_by(id=tank_id)
        tank = query.first()
        if not tank:
            abort(404)

        charts = tank.tank_charts

        if not charts:
            return redirect(url_for('admin.no_tank_charts_edit', tank_id=tank.id))

        return render_template("admin/tanks/edit.html", charts=charts, tank=tank)

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

@admin_bp.route('/add-pretrip-model', methods=["POST", "GET"])
def add_pretrip_model():
    if request.method == "GET":
        return render_template('admin/pretrip/add-pretrip-model.html')

@admin_bp.route('/pretrip/validate-headers', methods=['POST'])
def pretrip_validate_headers_route():
    """
    API endpoint to validate the column headers of a CSV file.
    Expects a JSON payload with a "columns" key: {"columns": ["col1", "col2", ...]}
    """
    json_data = request.get_json()
    if not json_data or 'columns' not in json_data:
        return jsonify({"error": "Invalid request. JSON body must contain a 'columns' key."}), 400

    column_names = json_data['columns']
    is_valid, message = validate_csv_headers(column_names)

    if not is_valid:
        # Return a 400 Bad Request status if validation fails
        return jsonify({
            "error": message,
            "status": "error",
            'valid': False
            }), 400

    # If validation succeeds, return a 200 OK status
    return jsonify({
        "message": message,
        "status": "success",
        "valid": True
        }), 200

@admin_bp.route('/pretrip/check-blueprint-name', methods=['GET'])
def check_blueprint_name():
    name = request.args.get('name', '').strip()
    if not name:
        return jsonify({"error": "Name parameter is required."}), 400

    exists = db.session.query(Blueprint.query.filter_by(name=name).exists()).scalar()
    return jsonify({"exists": exists})

from flask_app.models.pretrip import Blueprint, BlueprintItem

@admin_bp.route('/pretrip/blueprint-payload-upload', methods=['POST'])
def pretrip_blueprint_payload_upload():
    payload_str = request.form.get('payload')
    if not payload_str:
        return jsonify({"error": "Invalid request. Form must contain a 'payload' key."}), 400

    try:
        json_data = json.loads(payload_str)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON in payload."}), 400

    if 'rows' not in json_data or 'name' not in json_data:
        return jsonify({"error": "Invalid request. JSON body must contain 'rows' and 'name' keys."}), 400

    rows = json_data['rows']
    blueprint_name = json_data['name']
    override = json_data.get('override', False)

    # Basic validation
    if not blueprint_name or not isinstance(blueprint_name, str):
        return jsonify({"error": "Invalid blueprint name provided."}), 400
    if not rows or not isinstance(rows, list):
        return jsonify({"error": "Invalid rows data provided."}), 400

    try:
        existing_blueprint = Blueprint.query.filter_by(name=blueprint_name).first()

        if existing_blueprint:
            if override:
                # Delete existing items for the blueprint
                for item in existing_blueprint.items:
                    db.session.delete(item)
                db.session.flush() # Ensure deletions are processed before adding new items
                new_blueprint = existing_blueprint # Use the existing blueprint object
            else:
                return jsonify({"error": f"A blueprint with the name '{blueprint_name}' already exists. Use override option to replace."}), 409
        else:
            # Create a new Blueprint
            new_blueprint = Blueprint(name=blueprint_name)
            db.session.add(new_blueprint)
            db.session.flush()  # Flush to get the new_blueprint.id for the items

        # Create BlueprintItems
        for item_data in rows:
            new_item = BlueprintItem(
                blueprint_id=new_blueprint.id,
                section=item_data.get('section'),
                name=item_data.get('inspection_item'),
                details=item_data.get('details'),
                notes=item_data.get('notes'),
                date_field_required=item_data.get('date_required', False),
                numeric_field_required=item_data.get('numeric_required', False),
                boolean_field_required=item_data.get('boolean_field_required', False),
                text_field_required=item_data.get('text_field_required', False)
            )
            db.session.add(new_item)

        db.session.commit()

        # Instead of returning JSON, render the summary page
        print(f"Attempting to render template for blueprint: {new_blueprint}")
        return render_template(
            'admin/pretrip/blueprint_creation_summary.html',
            blueprint=new_blueprint
        )

    except Exception as e:
        db.session.rollback()
        import traceback
        print("Error creating blueprint:")
        traceback.print_exc()
        # In a production app, you'd log this error more robustly.
        return jsonify({"error": "An internal error occurred while creating the blueprint."}), 500
