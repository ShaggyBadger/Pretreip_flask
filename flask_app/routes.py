from flask import render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_app.app_constructor import app
import flask_app.models
from datetime import timedelta

app.permanent_session_lifetime = timedelta(days=7)

@app.before_request
def refresh_session():
	'''
	set this to True if you want to allow users to remain signed in for 7 days
	'''
	session.permanent = True

@app.route('/')
def home():
	if 'user_id' in session:
		return render_template('dashboard.html')
	return render_template('home_guest.html')

@app.route('/failed_login')
def failed_login():
	return render_template('failed_login.html')
	
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form.get('username')
		password = request.form.get('password')
		
		utils_obj = models.Utils()
		user = utils_obj.check_password(
			username,
			password
			)
		
		if user:		
			session['user_id'] = user[0]
			session['username'] = username
			url = url_for('home')
			
			return redirect(url)
		
		else:
			url = url_for('failed_login')
			
			return redirect(url)
		
	return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		username = request.form.get('username')
		password = request.form.get('password')
		
		utils_obj = models.Utils()
		user_id = utils_obj.register_user(
			username,
			password
			)
		
		# register_user method returns True if user already exists in db
		print(f'\n\n*****\n{utils_obj.user_exists}\n*****\n\n')
		if utils_obj.user_exists is True:
			url = url_for('failed_register')
			
			return redirect(url)
		
		# register_user method returns 
		else:
			session['user_id'] = user_id
			session['username'] = username
			url = url_for('home')
			
			return redirect(url)
	return render_template('register.html')

@app.route('/failed_register')
def failed_register():
	return render_template('failed_register.html')

@app.route('/logout')
def logout():
	session.clear()  # This clears all session data
	return redirect(url_for('home'))

