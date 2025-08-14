from flask_app.models import TankCharts, TankData, StoreData, StoreTankMap
from flask import render_template, request, jsonify, redirect, abort, url_for, session as flask_session
from flask_app.models import Users
from admin_app import admin_bp

@admin_bp.route('/')
def home():
    for i in flask_session:
        print(i)
    user_id = flask_session['user_id']
    username = flask_session['username']
    role = flask_session['role']
    print(user_id)
    print(username)
    print(role)
    query = Users.query
    query = query.filter(Users.driver_id == 30150643)
    user = query.all()
    return render_template('admin/home.html')

