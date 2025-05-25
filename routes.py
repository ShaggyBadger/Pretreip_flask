from flask import render_template, request, redirect, url_for, session
from app import app
#from models import db, User  # Optional depending on what you're doing

@app.route('/')
def home():
	#if 'user_id' in session:
		#return render_template('home_logged_in.html')
	#return render_template('home_guest.html')
	return 'Hello World'
