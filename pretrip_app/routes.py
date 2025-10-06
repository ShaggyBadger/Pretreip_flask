from flask import render_template, request, redirect, url_for, session, current_app, flash
from platformdirs import user_cache_dir
from sqlalchemy import or_
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
    user_id = session.get('user_id')
    templates = PretripTemplate.query.filter(
        or_(PretripTemplate.user_id == user_id, PretripTemplate.user_id == None)
    ).all()
    return render_template('pretrip/manage_templates.html', templates=templates)

@pretrip_bp.route('/template/new', methods=['GET', 'POST'])
def new_template():
    return render_template('pretrip/new_template.html')

@pretrip_bp.route('/template/edit/<int:template_id>', methods=['GET'])
def edit_template(template_id):
    template = PretripTemplate.query.get_or_404(template_id)
    user_id = session.get('user_id')
    if template.user_id is not None and template.user_id != user_id:
        # Redirect to a new route for unauthorized access
        return redirect(url_for('pretrip_bp.unauthorized_template_access', template_id=template.id))
    return render_template('pretrip/edit_template.html', template=template)

@pretrip_bp.route('/template/unauthorized/<int:template_id>')
def unauthorized_template_access(template_id):
    template = PretripTemplate.query.get_or_404(template_id)
    return render_template('pretrip/unauthorized-template.html', template=template)


