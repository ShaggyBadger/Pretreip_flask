from flask import render_template, request, redirect, url_for, flash
from tankGauge_app import tankGauge_bp
from dbConnector import fetch_session
from .models import TankCharts, TankData, StoreData, StoreTankMap
from sqlalchemy import or_


@tankGauge_bp.route('/')
def home():
    return render_template('tankGauge/home.html')

@tankGauge_bp.route('/planning-selection')
def planning_selection():
    return render_template('tankGauge/planning-selection.html')

@tankGauge_bp.route('/planning-submit', methods=['POST'])
def planning_submit():
    store_number = request.form.get("store_number")
    fuel_types = request.form.getlist("fuel_types")  # Gets all selected checkboxes

    if not store_number or not fuel_types:
        flash("Please enter a store number and select at least one fuel type.")
        return redirect(url_for('tankGauge.planning_selection'))

    # get the store_data object for the usere's store_num entry
    with next(fetch_session()) as session:
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
            for m in tank_map_entry:
                tank_id = m.tank_id
                temp_dict = {
                    'tank_type_id': tank_id,
                    'store_num': store_number,
                    'fuel_type': fuel_type
                }

                tank_dict_list.append(temp_dict)
    for d in tank_dict_list:
        print(d)
            
        
        

    return render_template(
        'tankGauge/planning-submit.html',
        tanks = tank_dict_list
    )