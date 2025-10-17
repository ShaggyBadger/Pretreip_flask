import collections # Added for defaultdict
from datetime import datetime # Added for inspection_date
import json # Added for item_snapshot
from flask import render_template, request, redirect, url_for, session, current_app, flash, jsonify
from platformdirs import user_cache_dir
from sqlalchemy import or_
from . import pretrip_bp
from flask_app.models.pretrip import PretripTemplate, PretripItem, TemplateItem, Blueprint, PretripInspection, PretripResult # Added Blueprint, PretripInspection, PretripResult
from .forms import NewTemplateForm, NewItemForm
from flask_app.extensions import db

@pretrip_bp.before_request # Ensure user is logged in before accessing any pretrip routes
def require_login():
    # Allow certain routes to bypass login check if needed (e.g., public API endpoints)
    # For now, all pretrip routes require login.

    if 'user_id' not in session:
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'status': 'error', 'message': 'Authentication required.'}), 401
        else:
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
    return redirect(url_for('pretrip.list_inspections'))

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

@pretrip_bp.route('/inspections')
def list_inspections():
    user_id = session.get('user_id')
    if not user_id:
        flash('You must be logged in to view inspections.', 'danger')
        return redirect(url_for('auth_bp.login'))

    all_inspections = PretripInspection.query.filter_by(user_id=user_id, is_deleted=False).order_by(PretripInspection.inspection_datetime.desc()).all()

    inspections_data = []
    for inspection in all_inspections:
        passed_items = 0
        failed_items = 0
        overall_status = 'OK'

        for result in inspection.results:
            if result.severity == 'ok':
                passed_items += 1
            else:
                failed_items += 1
                if result.severity == 'action_required':
                    overall_status = 'Action Required'
                elif overall_status != 'Action Required': # Don't downgrade from Action Required
                    overall_status = 'Defects Found'
        
        # If no items, default to OK
        if not inspection.results:
            overall_status = 'N/A'

        inspections_data.append({
            'id': inspection.id,
            'date': inspection.inspection_datetime,
            'template_name': inspection.template.name if inspection.template else 'N/A',
            'equipment': inspection.equipment.name if inspection.equipment else 'N/A',
            'passed_items': passed_items,
            'failed_items': failed_items,
            'overall_status': overall_status
        })

    return render_template('pretrip/inspections.html', inspections=inspections_data)

@pretrip_bp.route('/inspect/select-template')
def select_inspection_template():
    user_id = session.get('user_id')
    templates = PretripTemplate.query.filter(
        PretripTemplate.is_deleted == False,
        or_(PretripTemplate.user_id == user_id, PretripTemplate.user_id == None)
    ).all()
    return render_template('pretrip/select_template.html', templates=templates)

@pretrip_bp.route('/inspect/<int:template_id>')
def inspect_form(template_id):
    template = PretripTemplate.query.get_or_404(template_id)
    user_id = session.get('user_id')
    if template.user_id is not None and template.user_id != user_id:
        return redirect(url_for('pretrip.unauthorized_template_access', template_id=template.id))

    items_by_section = collections.defaultdict(list)
    for item in sorted(template.items, key=lambda item: item.display_order):
        section_name = item.section if item.section else "Uncategorized"
        items_by_section[section_name].append(item)

    sorted_sections = sorted(items_by_section.items())

    return render_template('pretrip/form.html', template=template, sorted_sections=sorted_sections)

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

@pretrip_bp.route('/inspection/view/<int:inspection_id>', methods=['GET'])
def view_inspection(inspection_id):
    inspection = PretripInspection.query.get_or_404(inspection_id)
    user_id = session.get('user_id')

    # Critical: Check for unauthorized access if inspections are user-specific
    if inspection.user_id != user_id:
        flash('You are not authorized to view this inspection.', 'danger')
        return redirect(url_for('pretrip.home')) # Redirect to pretrip home or an unauthorized page

    return render_template('pretrip/view_inspection.html', inspection=inspection)

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

@pretrip_bp.route('/api/pretrip/inspect/submit', methods=['POST'])
def submit_inspection():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'User not logged in.'}), 401

    template_id = request.form.get('template_id')
    if not template_id:
        return jsonify({'status': 'error', 'message': 'Template ID is missing.'}), 400

    template = PretripTemplate.query.get_or_404(template_id)

    try:
        # Create a new PretripInspection record
        new_inspection = PretripInspection(
            template_id=template.id,
            user_id=user_id,
            inspection_datetime=datetime.utcnow() # Use current UTC time
        )
        db.session.add(new_inspection)
        db.session.flush() # Flush to get the inspection ID

        # Process each item in the form
        for key, value in request.form.items():
            if key.startswith('item_id_'):
                item_id = key.replace('item_id_', '')
                item = TemplateItem.query.get(item_id)

                if item:
                    # Capture item snapshot
                    item_snapshot = {
                        'id': item.id,
                        'name': item.name,
                        'details': item.details,
                        'notes': item.notes,
                        'section': item.section,
                        'display_order': item.display_order,
                        'date_field_required': item.date_field_required,
                        'numeric_field_required': item.numeric_field_required,
                        'boolean_field_required': item.boolean_field_required,
                        'text_field_required': item.text_field_required,
                    }

                    # Extract form data for this item
                    has_problem = request.form.get(f'has_problem_{item_id}') == 'on' # Checkbox value is 'on' if checked

                    if has_problem:
                        status = request.form.get(f'status_{item_id}')
                        notes = request.form.get(f'notes_{item_id}')
                    else:
                        status = 'ok'
                        notes = None # Or an empty string, depending on desired behavior

                    date_value = request.form.get(f'date_value_{item_id}')
                    numeric_value = request.form.get(f'numeric_value_{item_id}')
                    boolean_value = request.form.get(f'boolean_value_{item_id}') == 'True'
                    text_value = request.form.get(f'text_value_{item_id}')

                    # Create PretripResult
                    new_result = PretripResult(
                        inspection_id=new_inspection.id,
                        item_id=item.id,
                        severity=status, # Corrected argument name
                        notes=notes,
                        date_value=datetime.strptime(date_value, '%Y-%m-%d') if date_value else None,
                        numeric_value=float(numeric_value) if numeric_value else None,
                        boolean_value=boolean_value,
                        text_value=text_value,
                        item_snapshot=json.dumps(item_snapshot) # Store snapshot as JSON string
                    )
                    db.session.add(new_result)

        db.session.commit()
        redirect_url = url_for('pretrip.view_inspection', inspection_id=new_inspection.id)
        return jsonify({'status': 'success', 'message': 'Inspection submitted successfully.', 'redirect_url': redirect_url}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error submitting inspection: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to submit inspection.'}), 500

@pretrip_bp.route('/api/pretrip/inspection/delete/<int:inspection_id>', methods=['POST'])
def delete_inspection_api(inspection_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'User not logged in.'}), 401

    inspection = PretripInspection.query.get_or_404(inspection_id)

    # Critical: Add authorization check if only the creator can delete
    if inspection.user_id != user_id:
        return jsonify({'status': 'error', 'message': 'Unauthorized to delete this inspection.'}), 403

    try:
        inspection.is_deleted = True
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Inspection deleted successfully.'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error soft-deleting inspection {inspection_id}: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to delete inspection.'}), 500

