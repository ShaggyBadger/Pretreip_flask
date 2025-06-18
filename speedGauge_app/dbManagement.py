import sqlite3
import pandas as pd
from flask_app import settings
from datetime import datetime

class DbManagement:
	def __init__(self):
		pass
	def db_conn(self):
		'''easy way to establish a db connection inside this class'''
		conn = sqlite3.connect(settings.db_name, timeout=10)
		return conn
	def get_dates(self):
		'''
		Returns a list full of  start_date in ASC order. oldest date is first, newest date is index[-1]
		
		the date is str from db, it can be used for query and also turned into datetime object later
		'''	
		conn = self.db_conn()
		c = conn.cursor()
		
		sql = '''
		SELECT DISTINCT start_date
		FROM speedGauge_data
		ORDER BY start_date ASC
		'''
		c.execute(sql)
		datelist = [
			date[0] for date
			in c.fetchall()
			]
		c.fetchall()
		conn.close()
		
		return datelist
	def get_all_driver_id(self):
		conn = self.db_conn()
		c = conn.cursor()
		
		sql = '''
		SELECT DISTINCT driver_id
		FROM speedGauge_data
		'''
		c.execute(sql)
		id_list = [
			id[0] for id
			in c.fetchall()
			]
		
		conn.close()
		return id_list
	def gen_interpolated_speeds(self):
		'''
		This will go through entire database and look for missing percent_speedings then generate
		some interpolated values to fill in the gap
		'''
		datelist = self.get_dates()
		id_list = self.get_all_driver_id()		
		
		conn = self.db_conn()
		c = conn.cursor()
		
		sql = '''
		SELECT
		  driver_id,
		  start_date,
		  percent_speeding
		FROM speedGauge_data
		'''
		c.execute(sql)
		all_rows = c.fetchall()
		conn.close()
		
		main_dict = {}
		
		for row in all_rows:
			if row[0] in main_dict:
				sub_dict = main_dict[row[0]]
				sub_dict[row[1]] = row[2]
			else:
				main_dict[row[0]] = {
					row[1]: row[2]
				}
		
		for driver in main_dict:
			d_dict = main_dict[driver]
			for date in datelist:
				if date not in d_dict:
					d_dict[date] = None
		
		
		test_dict = main_dict[1201619]
		for date in datelist:
			print(date, test_dict[date])
		
		
		
		
