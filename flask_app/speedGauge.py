import pandas as pd
import re
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from flask_app import settings


class Processor():
	def __init__(self):
		pass
	
	def standard_flow(self):
		self.create_table_from_json()
		
	def create_table_from_json(self, json_file=None, table_name='speedGauge', debug=False):
		# default to the pre_made json file if none is provided
		if json_file is None:
			json_file = settings.SPEEDGAUGE_DIR / 'speedGauge_table.json'
			
		# Load JSON data from file
		with open(json_file, 'r') as file:
			column_info = json.load(file)
			
			# Construct SQL CREATE TABLE statement
			columns_sql = ",\n    ".join([f'"{column}" {datatype}' for column, datatype in column_info.items()])
			
			create_table_sql = f'''
			CREATE TABLE IF NOT EXISTS "{table_name}" (
				{columns_sql}
				);
			'''
			
			# Print the SQL for debugging
			if debug is True:
				print("Executing SQL:\n", create_table_sql)
			
			# Connect to the database and execute SQL
			conn = self.db_conn()
			c = conn.cursor()
			c.execute(create_table_sql)
			
			if self.check_tbl_exists(table_name):
				print('Table already exists\n')
			else:
				conn.commit()
				print('Table is constructed in the database. yw\n')
			
			conn.close()
	
	def find_unprocessed_files(self):
		'''
		returns a list of all files in the unprocessed folder
		'''
		file_list = []
		
		for file in settings.UNPROCESSED_SPEEDGAUGE_PATH.iterdir():
			if file.is_file():
				file_list.append(file)
		
		return file_list
	
	
	def extract_data(self, csv_file):
		df = pd.read_csv(csv_file)
		
		# make list to hold dictionaries
		dict_list = []
		
		# convert rows to dictionaries
		for index, row in df.iterrows():
			row_dict = row.to_dict()
			driver_name = row_dict['driver_name']
	
			# break once we get to this part
			# of spreadsheet
			if driver_name == '---':
				break
			
			valid_name = True
			
			if driver_name == 'median':
				valid_name = False
			
			if driver_name[0].isdigit():
				valid_name = False
			
			if valid_name is True:
				dict_list.append(row_dict)
		
		return dict_list
	
	def parse_timestamp(self, date):
		print(date)
	
	def check_tbl_exists(self, tbl_name):
		conn = self.db_conn()
		c = conn.cursor()
		
		sql = '''
		SELECT * FROM sqlite_master WHERE type='table' AND name=?
		'''
		value = (tbl_name,)
		c.execute(sql, value)
		result = c.fetchone()
		conn.close()
		
		if result:
			return True
		
		else:
			return False
	
	def db_conn(self):
		conn = sqlite3.connect(settings.db_name)
		
		return conn
		
