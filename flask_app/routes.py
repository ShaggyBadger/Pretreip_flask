from flask import render_template, request, redirect, url_for, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_app.app_constructor import app
from flask_app import models
from flask_app import settings
from datetime import timedelta
import speedGauge_app as sga

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
      session['user_id'] = user['id']
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

@app.route('/tempUpload', methods=['GET', 'POST'])
def tempUpload():
  if request.method == 'POST':
    file = request.files.get('file')
    destination = settings.UNPROCESSED_SPEEDGAUGE_PATH / file.filename
    file.save(destination)
  return render_template('tempUpload.html')

@app.route('/speedgauge', methods=['GET', 'POST'])
def speedGauge():
  if 'user_id' in session:
    user_id = session['user_id']
    db_model = current_app.db_model
    
    # use the user id from this session to locate driver_id
    driver_id = db_model.retrieve_driver_id(user_id)
    
    if request.method == 'POST':
      pass
    else:
      # build api object
      sg_api = sga.SpeedgaugeApi.Api(driver_id, db_model)
      
      # get material to test
      a = sg_api.build_speedgauge_report()
      
      # get list of dates
      dates = sg_api.get_dates()
      
      # get latest date
      display_date = dates[-1]
      
      # get row data for display date
      row_data = sg_api.get_speedGauge_row(display_date)
      
      return render_template('speedgauge.html', info=row_data)
      

    return  render_template('speedgauge.html')
  else:
    url = url_for('home')
    return redirect(url)

@app.route('/speedgauge2', methods=['GET', 'POST'])
def speedGauge2():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    db_model = current_app.db_model
    driver_id = db_model.retrieve_driver_id(user_id)

    sg_api = sga.SpeedgaugeApi.Api(driver_id, db_model)
    sg_data = sg_api.build_speedgauge_report()
    
    '''gather data for template context'''
    # store user-requested date
    selected_date = request.args.get('start_date')
    
    # build lost of dates
    available_dates = [
      entry['start_date']
      for entry in sg_data
      ]
      
    # default to most recent date
    selected_data = available_dates[0]
    
    # get selected date if requested
    if selected_date:
      print('\n*****\nselected date')
      print(f'type: {type(selected_date)}')
      print(f'content: {selected_date}')
        selected_data = next((entry for entry in sg_data if entry['start_date'] == selected_date), None)

    return render_template(
        'speedgauge2.html',
        available_dates=available_dates,
        selected_date=selected_date,
        selected_data=selected_data
    )

@app.route('/routes_debug')
def routes_debug():
    return '<br>'.join(str(rule) for rule in app.url_map.iter_rules())
