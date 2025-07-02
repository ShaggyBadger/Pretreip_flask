import sqlite3
import json
import pandas as pd
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from flask_app import settings

class DbAudit:
  '''
  A class that can run checks and stuff in the db
  '''
  def __init__(self):
    pass
  def db_conn(self):
    '''easy way to establish a db connection inside this class'''
    conn = sqlite3.connect(settings.db_name, timeout=10)
    return conn
  def chk_num_entries(self):
    '''
    runs a quick check to see how many rows are in the table
    '''
    conn = self.db_conn()
    c = conn.cursor()
    
    sql = '''
    SELECT id
    FROM speedGauge_data
    '''
    c.execute(sql)
    results = c.fetchall()
    conn.close()
    
    print(f'Number of entries in the speedGauge_data table: {len(results)}')
  def gather_driver_data(self, driver_id=30150643):
    conn = self.db_conn()
    c = conn.cursor()
    
    sql = '''
    SELECT percent_speeding 
    FROM speedGauge_data
    WHERE driver_id = ?
    '''
    value = (driver_id,)
    c.execute(sql, value)
    results = c.fetchall()
    conn.close()
    
    print(len(results))
    print(results[4])
