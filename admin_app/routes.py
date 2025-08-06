from tankGauge_app.models import TankCharts, TankData, StoreData, StoreTankMap
from flask import render_template, request, jsonify, redirect, abort, url_for, session as flask_session
from .models import Users
from admin_app import admin_bp

@admin_bp.route('/')
def home():
    return render_template('admin/home.html')

