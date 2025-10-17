from flask import render_template, request, redirect, url_for, session, current_app, flash
from . import auth_bp
from . import utils

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        utils_obj = utils.Utils()
        user = utils_obj.register_user(
            username=email,
            password=password
        )

        if user is None:
            flash('An account with that email already exists.')
            return redirect(url_for('auth_bp.failed_register'))
        else:
            # Log the user in immediately
            # user object is already available
            session['user_id'] = user.id
            session['username'] = user.username
            session['admin_level'] = user.admin_level
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
            print(f"DEBUG: User object after login: {user}")
            print(f"DEBUG: User admin_level after login: {user.admin_level}")
            session['user_id'] = user.id
            session['username'] = user.username
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