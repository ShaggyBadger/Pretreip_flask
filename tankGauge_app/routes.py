from flask import render_template, request, redirect, url_for, flash, session as flask_session
import flask
from tankGauge_app import tankGauge_bp
from dbConnector import fetch_session
from .models import TankCharts, TankData, StoreData, StoreTankMap
from sqlalchemy import or_
import json


@tankGauge_bp.route('/')
def home():
    if "user_id" not in flask_session:
        return redirect(url_for("home"))
    
    return render_template('tankGauge/home.html')

@tankGauge_bp.route('/planning')
def planning_selection():
    if "user_id" not in flask_session:
        return redirect(url_for("home"))
    return render_template('tankGauge/planning.html')

@tankGauge_bp.route('/planning-submit', methods=['POST'])
def planning_submit():
    if "user_id" not in flask_session:
        return redirect(url_for("home"))
    
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
                query = session.query(TankCharts.inches, TankCharts.gallons).filter(TankCharts.tank_type_id == tank_id)
                tank_chart = query.all()
                chart_dict = {inch: gallon for inch, gallon in tank_chart}

                temp_dict = {
                    'tank_type_id': tank_id,
                    'store_num': store_number,
                    'fuel_type': fuel_type,
                    'tank_chart': chart_dict
                }

                tank_dict_list.append(temp_dict)

    return render_template(
        'tankGauge/planning-submit.html',
        tanks = tank_dict_list
    )