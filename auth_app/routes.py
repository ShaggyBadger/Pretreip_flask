from flask import render_template, request, redirect, url_for, session, current_app, flash
from . import auth_bp
from flask_app import utils

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        driver_id = request.form.get('driver_id')
        dot_number = request.form.get('dot_number')

        # Determine role based on DOT number
        authorized_dots = current_app.config.get('AUTHORIZED_DOT_NUMBERS', [])
        role = 'premium' if dot_number in authorized_dots else 'standard'

        utils_obj = utils.Utils()
        user_id = utils_obj.register_user(
            username=email,
            password=password,
            driver_id=driver_id,
            dot_number=dot_number,
            role=role
        )

        if user_id is None:
            flash('An account with that email already exists.')
            return redirect(url_for('auth_bp.failed_register'))
        else:
            # Log the user in immediately
            session['user_id'] = user_id
            session['username'] = email
            session['role'] = role
            return redirect(url_for('home'))

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier') # Can be email or driver_id
        password = request.form.get('password')

        utils_obj = utils.Utils()
        user = utils_obj.check_password(identifier, password)

        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['admin_level'] = user.admin_level
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.')
            return redirect(url_for('auth_bp.failed_login'))

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@auth_bp.route('/failed_login')
def failed_login():
    return render_template('auth/failed_login.html')

@auth_bp.route('/failed_register')
def failed_register():
    return render_template('auth/failed_register.html')