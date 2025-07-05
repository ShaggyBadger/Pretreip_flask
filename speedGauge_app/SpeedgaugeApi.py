import pymysql
import json
import pandas as pd
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from flask_app import settings, models

class Api:
  '''
  this is the main way to get the data for a user. should return dicts and stuff
  '''
  def __init__(self, driver_id, models_utils):
    self.driver_id = driver_id
    self.models_utils = models_utils
  
  def build_spedgauge_report(self):
  	'''
  	returns a dict:
  		key: start_date
  		value: speedgauge rows for that date
  	'''
  	date_list = self.get_dates()
  	for i in date_list:
  		print(i)
  
  def get_speedGauge_row(self, start_date):
    '''
    this takes in the start_date and returns the row of data in dict form from the db
    '''
    conn = self.models_utils.get_db_connection()
    c = conn.cursor()
    
    sql = '''
    SELECT *
    FROM speedGauge_data
    WHERE driver_id = %s AND
    start_date = %s;
    '''
    values = (self.driver_id, start_date)
    
    c.execute(sql, values)
    
    row_dict = c.fetchone()
    
    conn.close()
    
    return row_dict
  def get_dates(self, cuttoff_time=365):
    '''
    default cuttoff time is a year, although you can override if you want. just do it with num days
    
    Returns a list full of  start_date in ASC order. oldest date is first, newest date is index[-1]
    
    the date is str from db, it can be used for query and also turned into datetime object later
    '''
    cuttoff_date = datetime.now() - timedelta(days=cuttoff_time)
    
    conn = self.models_utils.get_db_connection()
    c = conn.cursor()
    
    sql = '''
    SELECT DISTINCT start_date
    FROM speedGauge_data
    ORDER BY start_date ASC
    '''
    c.execute(sql)
    datelist = c.fetchall()
    conn.close()
    
    filtered_list = []
    
    for date in datelist:
      start_date = date['start_date']
      
      if start_date is not None and start_date >= cuttoff_date:
        filtered_list.append(start_date.isoformat())
     
    return filtered_list
