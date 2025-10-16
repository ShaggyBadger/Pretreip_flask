import collections # Added for defaultdict
from flask import render_template, request, redirect, url_for, session, current_app, flash, jsonify
from platformdirs import user_cache_dir
from sqlalchemy import or_
from . import pretrip_bp
from flask_app.models.pretrip import PretripTemplate, PretripItem, TemplateItem, Blueprint # Added Blueprint
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
        PretripTemplate.is_deleted == False,
        or_(PretripTemplate.user_id == user_id, PretripTemplate.user_id == None)
    ).all()
    return render_template('pretrip/manage_templates.html', templates=templates)

@pretrip_bp.route('/template/new', methods=['GET', 'POST'])
def new_template():
    blueprints = Blueprint.query.all() # Query all blueprints
    return render_template('pretrip/new_template.html', blueprints=blueprints) # Pass blueprints to template

@pretrip_bp.route('/template/create-from-blueprint', methods=['POST'])
def create_template_from_blueprint():
    blueprint_id = request.form.get('blueprint_id')
    if not blueprint_id:
        flash('No blueprint selected.', 'danger')
        return redirect(url_for('pretrip.new_template'))

    blueprint = Blueprint.query.get_or_404(blueprint_id)
    
    # Group items by section and sort them
    items_by_section = collections.defaultdict(list)
    for item in sorted(blueprint.items, key=lambda item: item.id): # Sort items by ID first
        section_name = item.section if item.section else "Uncategorized"
        
        # Convert BlueprintItem object to a dictionary for JSON serialization
        item_data = {
            'id': item.id,
            'name': item.name,
            'details': item.details,
            'notes': item.notes,
            'date_field_required': item.date_field_required,
            'numeric_field_required': item.numeric_field_required,
            'boolean_field_required': item.boolean_field_required,
            'text_field_required': item.text_field_required,
            'section': item.section # Include section for completeness, though it's the key
        }
        items_by_section[section_name].append(item_data)

    # Sort sections by name
    sorted_sections = sorted(items_by_section.items())

    return render_template('pretrip/blueprint_review.html', blueprint=blueprint, sorted_sections=sorted_sections)

@pretrip_bp.route('/template/view/<int:template_id>', methods=['GET'])
def view_template(template_id):
    template = PretripTemplate.query.get_or_404(template_id)
    user_id = session.get('user_id')
    if template.user_id is not None and template.user_id != user_id:
        return redirect(url_for('pretrip.unauthorized_template_access', template_id=template.id))
    
    items_by_section = collections.defaultdict(list)
    for item in sorted(template.items, key=lambda item: item.display_order):
        section_name = item.section if item.section else "Uncategorized"
        items_by_section[section_name].append(item)

    sorted_sections = sorted(items_by_section.items())

    return render_template('pretrip/view_template.html', template=template, sorted_sections=sorted_sections)

@pretrip_bp.route('/template/edit/<int:template_id>', methods=['GET'])
def edit_template(template_id):
    template = PretripTemplate.query.get_or_404(template_id)
    user_id = session.get('user_id')
    if template.user_id is not None and template.user_id != user_id:
        # Redirect to a new route for unauthorized access
        return redirect(url_for('pretrip.unauthorized_template_access', template_id=template.id))
    
    items_by_section = collections.defaultdict(list)
    for item in sorted(template.items, key=lambda item: item.display_order):
        section_name = item.section if item.section else "Uncategorized"
        
        item_data = {
            'id': item.id,
            'name': item.name,
            'details': item.details,
            'notes': item.notes,
            'date_field_required': item.date_field_required,
            'numeric_field_required': item.numeric_field_required,
            'boolean_field_required': item.boolean_field_required,
            'text_field_required': item.text_field_required,
            'section': item.section
        }
        items_by_section[section_name].append(item_data)

    sorted_sections = sorted(items_by_section.items())

    return render_template('pretrip/edit_template.html', template=template, sorted_sections=sorted_sections)

@pretrip_bp.route('/template/unauthorized/<int:template_id>')
def unauthorized_template_access(template_id):
    template = PretripTemplate.query.get_or_404(template_id)
    return render_template('pretrip/unauthorized-template.html', template=template)


@pretrip_bp.route('/api/template/create-custom', methods=['POST'])
def create_custom_template():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Invalid JSON'}), 400

    user_id = session.get('user_id')
    
    # Create the new template
    new_template = PretripTemplate(
        name=data.get('name', 'Unnamed Template'),
        description=data.get('description', ''),
        user_id=user_id
    )
    db.session.add(new_template)

    item_order = 0
    for section_name, items in data.get('sections', {}).items():
        for item_data in items:
            template_item = TemplateItem(
                name=item_data.get('name'),
                details=item_data.get('details'),
                notes=item_data.get('notes'),
                section=section_name,
                display_order=item_order,
                date_field_required=item_data.get('date_field_required', False),
                numeric_field_required=item_data.get('numeric_field_required', False),
                boolean_field_required=item_data.get('boolean_field_required', False),
                text_field_required=item_data.get('text_field_required', False),
                template=new_template  # Associate with the template
            )
            db.session.add(template_item)
            item_order += 1

    try:
        db.session.commit()
        redirect_url = url_for('pretrip.view_template', template_id=new_template.id)
        return jsonify({'status': 'success', 'redirect_url': redirect_url})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating custom template: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to create template.'}), 500

@pretrip_bp.route('/api/template/delete/<int:template_id>', methods=['POST'])
def delete_template(template_id):
    template = PretripTemplate.query.get_or_404(template_id)
    user_id = session.get('user_id')

    if template.user_id != user_id:
        # Forbidden to delete templates that are not yours
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    try:
        template.is_deleted = True
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Template deleted'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting template: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to delete template.'}), 500

@pretrip_bp.route('/api/template/update/<int:template_id>', methods=['POST'])
def update_template(template_id):
    template = PretripTemplate.query.get_or_404(template_id)
    user_id = session.get('user_id')

    if template.user_id != user_id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Invalid JSON'}), 400

    try:
        template.name = data.get('name', template.name)
        template.description = data.get('description', template.description)

        # Delete existing items
        TemplateItem.query.filter_by(template_id=template.id).delete()

        item_order = 0
        for section_name, items in data.get('sections', {}).items():
            for item_data in items:
                template_item = TemplateItem(
                    name=item_data.get('name'),
                    details=item_data.get('details'),
                    notes=item_data.get('notes'),
                    section=section_name,
                    display_order=item_order,
                    date_field_required=item_data.get('date_field_required', False),
                    numeric_field_required=item_data.get('numeric_field_required', False),
                    boolean_field_required=item_data.get('boolean_field_required', False),
                    text_field_required=item_data.get('text_field_required', False),
                    template=template
                )
                db.session.add(template_item)
                item_order += 1
        
        db.session.commit()
        redirect_url = url_for('pretrip.view_template', template_id=template.id)
        return jsonify({'status': 'success', 'redirect_url': redirect_url})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating template: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to update template.'}), 500
