from flask import render_template, request, jsonify, redirect, url_for
from admin_app import admin_bp
from flask_app import settings
from flask_app.extensions import db
from flask_app.models.users import Users

# Import the refactored classes
from speedGauge_app.sgProcessor import Processor
from speedGauge_app.analytics import Analytics

@admin_bp.route('/')
def home():
    return render_template('admin/home.html')

@admin_bp.route('/upload_speedgauge', methods=['GET', 'POST'])
def upload_speedgauge():
    if request.method == 'GET':
        return render_template("admin/speedgauge/upload_speedgauge.html")

    if request.method == 'POST':
        file = request.files.get("file")
        if not file or file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        destination = settings.UNPROCESSED_SPEEDGAUGE_PATH / file.filename
        file.save(destination)

        try:
            # 1. Create instances of the refactored classes (no args needed)
            processor_obj = Processor()
            analytics_obj = Analytics()

            # 2. Run the standard flows. They will use the shared db.session.
            processor_obj.standard_flow()
            analytics_obj.standard_flow()

            return jsonify({"message": "File uploaded and processed successfully!"})

        except Exception as e:
            db.session.rollback()
            print(f"An error occurred during file processing: {e}")
            # It's good practice to log the full error
            import traceback
            traceback.print_exc()
            return jsonify({"error": "An internal error occurred during processing."}), 500

@admin_bp.route('/upload_success')
def upload_success():
    return render_template('admin/speedgauge/upload_success.html')

@admin_bp.route('/manage_users')
def manage_users():
    """Render the filter form for user management."""
    return render_template('admin/users/manage_users_form.html')

@admin_bp.route('/manage_users/search', methods=['POST'])
def manage_users_search():
    """Process the search POST and return a rendered HTML snippet of the user table."""
    filters = request.form
    query = Users.query

    if filters.get('first_name'):
        query = query.filter(Users.first_name.ilike(f"%{filters['first_name']}%"))
    if filters.get('last_name'):
        query = query.filter(Users.last_name.ilike(f"%{filters['last_name']}%"))
    if filters.get('driver_id'):
        query = query.filter(Users.driver_id.ilike(f"%{filters['driver_id']}%"))
    if filters.get('dot_number'):
        query = query.filter(Users.dot_number.ilike(f"%{filters['dot_number']}%"))
    if filters.get('admin_level'):
        try:
            admin_level = int(filters['admin_level'])
            query = query.filter(Users.admin_level == admin_level)
        except (ValueError, TypeError):
            pass # Ignore invalid admin_level
    if filters.get('role'):
        query = query.filter(Users.role.ilike(f"%{filters['role']}%"))

    users = query.limit(100).all()
    return render_template('admin/users/manage_users_table.html', users=users)

@admin_bp.route('/user/<int:user_id>/edit', methods=['GET'])
def edit_user(user_id):
    user = Users.query.get_or_404(user_id)
    return render_template('admin/users/edit_user_form.html', user=user)

@admin_bp.route('/user/<int:user_id>/update', methods=['POST'])
def update_user(user_id):
    user = Users.query.get_or_404(user_id)

    # Update user fields from form data
    user.username = request.form['username']
    user.first_name = request.form.get('first_name')
    user.last_name = request.form.get('last_name')
    user.driver_id = request.form.get('driver_id')
    user.dot_number = request.form.get('dot_number')
    user.admin_level = int(request.form.get('admin_level', 0)) # Default to 0 if not provided or invalid
    user.role = request.form.get('role')

    try:
        db.session.commit()
        # After update, re-render the table or a success message. For now, let's re-render the table.
        # This assumes the user will be redirected back to the search results.
        # A more sophisticated approach might involve returning a JSON success/error and letting JS handle it.
        # For now, let's return the updated user's row or a message.
        # Given the SPA nature, it's better to return a success message or re-render the form with a success message.
        # Or, as per the user's suggestion, return an HTML snippet. Let's return the updated user's form with a success message.
        return render_template('admin/users/edit_user_form.html', user=user, success_message="User updated successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error updating user {user_id}: {e}")
        return render_template('admin/users/edit_user_form.html', user=user, error_message="Error updating user.")

