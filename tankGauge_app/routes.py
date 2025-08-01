from flask import render_template, request, jsonify, redirect, abort, url_for, session as flask_session
from tankGauge_app import tankGauge_bp
from dbConnector import fetch_session
from .models import TankCharts, TankData, StoreData, StoreTankMap
from sqlalchemy import or_, func
import math


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

    # get the store_data object for the usere's store_num entry
    session = next(fetch_session())
    store_data = session.query(StoreData).filter(
    or_(
        StoreData.store_num == store_number,
        StoreData.riso_num == store_number
    )
    ).first()  # Use first() since only one store expected
    
    # get store_tank_map model obj
    tank_dict_list = []
    for fuel_type in fuel_types:
        tank_map_entry = (
        session.query(StoreTankMap)
        .filter_by(store_id=store_data.id, fuel_type=fuel_type)
        .all()
        )

        if tank_map_entry:
            for stm in tank_map_entry: # stm = StoreTankMap
                tank_id = stm.tank_id

                # build tank chart for this tank
                query = session.query(func.max(TankCharts.gallons))
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

    session.close()
    return render_template(
        'tankGauge/planning-submit.html',
        tanks = tank_dict_list,
        store_num = store_number
    )

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
    session = next(fetch_session())
    query = session.query(TankCharts.inches, TankCharts.gallons)
    query = query.filter(TankCharts.tank_type_id == tank_type_id)
    query = query.filter(TankCharts.gallons >= max_available_gal)
    query = query.order_by(TankCharts.gallons.asc())
    result = query.first()

    # do a try/except just in case somethine wierd happens with the query
    try:
        result_inch = result[0]
        result_gal = result[1]
        return jsonify(
            {
                'inch': result_inch,
                'gal': result_gal
            }
        )
    
    except:
        return jsonify(
            {
                "inch": None,
                'gal': None
            }
        )
    
    finally:
        session.close()

@tankGauge_bp.route('/delivery')
def delivery():
    if "user_id" not in flask_session:
        return redirect(url_for("home"))
    
    return render_template(url_for('tankGauge.delivery'))