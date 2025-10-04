from flask import render_template, request, redirect, url_for, session, current_app, flash
from . import pretrip_bp
from flask_app.models.pretrip import PretripTemplate, PretripItem, TemplateItem
from .forms import NewTemplateForm, NewItemForm
from flask_app.extensions import db

@pretrip_bp.before_request # Ensure user is logged in before accessing any pretrip routes
def require_login():
    if 'user_id' not in session:
        flash('You must be logged in to access this page.')
        return redirect(url_for('auth_bp.login'))

@pretrip_bp.route('/')
def home():
    return render_template('pretrip/index.html')

@pretrip_bp.route('/select-equipment')
def select_equipment():
    return render_template("pretrip/select_equipment.html")

@pretrip_bp.route('/history')
def history():
    return render_template("pretrip/history.html")

@pretrip_bp.route('/search')
def search():
    return render_template("pretrip/search.html")

@pretrip_bp.route('/templates')
def manage_templates():
    return render_template('pretrip/manage_templates.html')

@pretrip_bp.route('/template/new', methods=['GET', 'POST'])
def new_template():
    return render_template('pretrip/new_template.html')


