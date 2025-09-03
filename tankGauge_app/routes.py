from flask import render_template, request, jsonify, redirect, abort, url_for, session as flask_session
from tankGauge_app import tankGauge_bp
from flask_app.extensions import db
from flask_app.models import TankCharts, TankData, StoreData, StoreTankMap
from sqlalchemy import or_, func
import math
from rich.traceback import install
from rich import print
install()


@tankGauge_bp.route('/')
def home():
    if "user_id" not in flask_session:
        return redirect(url_for("home"))
    
    return render_template('tankGauge/home.html')

@tankGauge_bp.route('/planning')
def planning_selection():
    if "user_id" not in flask_session:
        return abort(404)
    return render_template('tankGauge/planning.html')

@tankGauge_bp.route('/planning-submit', methods=['POST'])
def planning_submit():
    if "user_id" not in flask_session:
        return abort(404)
    
    store_number = request.form.get("store_number")
    fuel_types = request.form.getlist("fuel_types")  # Gets all selected checkboxes

    if not store_number or not fuel_types:
        return redirect(url_for('tankGauge.planning_selection'))

    try:
        store_number_int = int(store_number)
    except (ValueError, TypeError):
        return render_template('tankGauge/missing-chart.html')

    # get the store_data object for the usere's store_num entry
    store_data = db.session.query(StoreData).filter(StoreData.store_num == store_number_int).first()
    if not store_data:
        store_data = db.session.query(StoreData).filter(StoreData.riso_num == store_number_int).first()
    if not store_data:
        return render_template('tankGauge/missing-chart.html')

    # get store_tank_map model obj
    tank_dict_list = []

    try:
        for fuel_type in fuel_types:
            tank_map_entry = (
            db.session.query(StoreTankMap)
            .filter_by(store_id=store_data.id, fuel_type=fuel_type)
            .all()
            )

            if tank_map_entry:
                for stm in tank_map_entry: # stm = StoreTankMap
                    tank_id = stm.tank_id

                    # build tank chart for this tank
                    try:
                        query = db.session.query(func.max(TankCharts.gallons))
                        query = query.filter(TankCharts.tank_type_id == tank_id)
                        max_gal = query.first()[0]
                        if not max_gal:
                            print(f"No tank chart found for tank_id: {tank_id}")
                            continue
                        ninety_percent = math.floor(max_gal * 0.9)

                        temp_dict = {
                            'tank_type_id': tank_id,
                            'store_num': store_number,
                            'fuel_type': fuel_type,
                            'max_gal': max_gal,
                            'ninety_percent': ninety_percent
                        }

                        tank_dict_list.append(temp_dict)
                    except Exception as e:
                        continue
        
        if not tank_dict_list:
            return render_template('tankGauge/missing-chart.html')

        return render_template(
        'tankGauge/planning-submit.html',
        tanks = tank_dict_list,
        store_num = store_number
        )

    except Exception as e:
        return render_template('tankGauge/missing-chart.html')

@tankGauge_bp.route('/calculate_inches', methods=['POST'])
def calculate_inches():
    if "user_id" not in flask_session:
        return abort(404)
    
    # get the data that ajax is sending
    data = request.get_json()
    gallons = data.get("gallons")
    tank_type_id = data.get('tank_type_id')
    max_gal = data.get('max_gal')

    # determine max allowable gallons that will fit
    max_available_gal = math.floor(max_gal * 0.9) - gallons

    # hit up the db
    query = db.session.query(TankCharts.inches, TankCharts.gallons)
    query = query.filter(TankCharts.tank_type_id == tank_type_id)
    query = query.filter(TankCharts.gallons >= max_available_gal)
    query = query.order_by(TankCharts.gallons.asc())
    result = query.first()

    # run a query to get all inches and gallons. this prob is innefficient
    # maybe wrap them up into ine query later
    query = TankCharts.query
    query = query.filter(
        TankCharts.tank_type_id == tank_type_id
        )
    query = query.order_by(
        TankCharts.inches.asc()
        )
    full_chart = query.all()
    inch_list = [row.inches for row in full_chart]
    gal_list = [row.gallons for row in full_chart]

    # do a try/except just in case somethine wierd happens with the query
    try:
        result_inch = result[0]
        result_gal = result[1]
        return jsonify(
            {
                'inch': result_inch,
                'gal': result_gal,
                'inch_list': inch_list,
                'gal_list': gal_list
            }
        )
    
    except:
        return jsonify(
            {
                "inch": None,
                'gal': None,
                'inch_list': [],
                'gal_list': []
            }
        )

@tankGauge_bp.route('/delivery')
def delivery():
    if "user_id" not in flask_session:
        return redirect(url_for("home"))
    
    return render_template('tankGauge/delivery.html')

@tankGauge_bp.route('/delivery-submit', methods=['POST'])
def delivery_submit():
    if "user_id" not in flask_session:
        return redirect(url_for("home"))
    
    store_number = request.form.get("store_number")
    fuel_types = request.form.getlist("fuel_types")  # Gets all selected checkboxes

    if not store_number or not fuel_types:
        return redirect(url_for('tankGauge.planning_selection'))

    try:
        store_number_int = int(store_number)
    except (ValueError, TypeError):
        return render_template('tankGauge/missing-chart.html')

    # get the store_data object for the usere's store_num entry
    store_data = db.session.query(StoreData).filter(StoreData.store_num == store_number_int).first()
    if not store_data:
        store_data = db.session.query(StoreData).filter(StoreData.riso_num == store_number_int).first()

    # get store_tank_map model obj
    tank_dict_list = []

    try:
        for fuel_type in fuel_types:
            tank_map_entry = (
            db.session.query(StoreTankMap)
            .filter_by(store_id=store_data.id, fuel_type=fuel_type)
            .all()
            )

            if tank_map_entry:
                for stm in tank_map_entry: # stm = StoreTankMap object
                    tank_id = stm.tank_id

                    # build tank chart for this tank
                    query = db.session.query(func.max(TankCharts.gallons))
                    query = query.filter(TankCharts.tank_type_id == tank_id)
                    max_gal = query.first()[0]
                    ninety_percent = math.floor(max_gal * 0.9)

                    temp_dict = {
                        'tank_type_id': tank_id,
                        'store_num': store_number,
                        'fuel_type': fuel_type,
                        'max_gal': max_gal,
                        'ninety_percent': ninety_percent
                    }

                    tank_dict_list.append(temp_dict)

    except:
        return render_template('tankGauge/missing-chart.html')

    return render_template(
        'tankGauge/delivery-submit.html',
        tanks=tank_dict_list,
        store_num=store_number
    )

@tankGauge_bp.route('/estimate_delivery_values', methods=['POST'])
def estimate_delivery_values():
    if "user_id" not in flask_session:
        return abort(404)
    
    # get the data that ajax is sending
    data = request.get_json()
    deliver_gallons = data.get("delivery_gallons")
    tank_inches = data.get("current_inches")
    tank_type_id = data.get('tank_type_id')

    # hit up the db
    query = db.session.query(TankCharts.gallons)
    query = query.filter(TankCharts.tank_type_id == tank_type_id)
    query = query.filter(TankCharts.inches == tank_inches)
    gallons_in_tank = query.first()
    
    try:
        final_gal = gallons_in_tank[0] + deliver_gallons
        query = db.session.query(TankCharts.inches)
        query = query.filter(TankCharts.tank_type_id == tank_type_id)
        query = query.filter(TankCharts.gallons <= final_gal)
        query = query.order_by(TankCharts.inches.desc())
        final_inch = query.first()[0]

        return jsonify(
            {
                'final_inches': final_inch,
                'final_gallons': final_gal,
                'starting_gallons': gallons_in_tank[0],
                'starting_inches': tank_inches
            }
        )
    
    except:
        return jsonify(
            {
                "inch": None,
                'gal': None
            }
        )
