import sqlite3
import json
import pandas as pd
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from flask_app import settings

class Api:
	'''
	this is the main way to get the data for a user. should return dicts and stuff
	'''
	def __init__(self, driver_id):
		self.driver_id = driver_id
	def db_conn(self):
		'''easy way to establish a db connection inside this class'''
		conn = sqlite3.connect(settings.db_name, timeout=10)
		return conn
	def get_speedGauge_row(self, start_date):
		'''
		this takes in the start_date and returns the row of data in dict form from the db
		'''
		conn = self.db_conn()
		c = conn.cursor()
		
		sql = '''
		SELECT *
		FROM speedGauge_data
		WHERE driver_id = ? AND
		start_date = ?;
		'''
		values = (self.driver_id, start_date)
		
		c.execute(sql, values)
		
		# get columns names
		col_names = [
			i[0] for i
			in c.description
			]
		
		# get row info for columns
		row_data = [
			i for i
			in c.fetchone()
		]
		
		conn.close()
		
		row_dict = dict(zip(col_names, row_data))
		return row_dict
	def get_dates(self, cuttoff_time=365):
		'''
		default cuttoff time is a year, although you can override if you want. just do it with num days
		
		Returns a list full of  start_date in ASC order. oldest date is first, newest date is index[-1]
		
		the date is str from db, it can be used for query and also turned into datetime object later
		'''
		cuttoff_date = datetime.now() - timedelta(days=cuttoff_time)
		
		conn = self.db_conn()
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
			start_date = datetime.fromisoformat(date[0])
			
			if start_date >= cuttoff_date:
				filtered_list.append(date[0])
		 
		return filtered_list
