import sqlite3
import json
import pandas as pd
import re
from datetime import datetime
from pathlib import Path
from flask_app import settings


class Processor():
	def __init__(self):
		pass
	
	def standard_flow(self):
		'''Method that will process the csv files in an orderly manner'''
		files = self.find_unprocessed_files()
		for csv_file in files:
			extracted_data = self.extract_data(csv_file)
			date_info = self.extract_date(csv_file)
	
	def find_unprocessed_files(self):
		'''
		returns a list of all files in the unprocessed folder
		'''
		file_list = []
		
		for file in settings.UNPROCESSED_SPEEDGAUGE_PATH.iterdir():
			if file.is_file():
				file_list.append(file)
		
		return file_list
	def extract_date(self, csv_file):
		'''
		this is chatGPT wizardry. idk how it works, but it does so dont mess with it
		'''
		df = pd.read_csv(csv_file)
		# Find the index of the row with '---'
		separator_index = df[df.iloc[:, 0] == '---'].index[0]
	
		# Date is 3ish rows below the
		# separator
		date_range = df.iloc[separator_index + 3, 0]
		print(date_range)
		print(type(date_range))
		input('stop here')
		
		# send the string to a cleaning
		# function
		date_string = self.parse_timestamp(date_range)
		
		# Define a regex to capture the two date components
		date_pattern = r"(\w+, \w+ \d{1,2}, \d{4}, \d{2}:\d{2})"
		matches = re.findall(date_pattern, date_string)
		
		if len(matches) == 2:
			# Parse the matched date strings
			start_date_str, end_date_str = matches
			
			# Define the format matching the date string
			date_format = "%A, %B %d, %Y, %H:%M"
			
			# Convert to datetime objects
			start_date = datetime.strptime(start_date_str, date_format)
			end_date = datetime.strptime(end_date_str, date_format)
			
			# Format as "YYYY-MM-DD HH:MM" for storage in SQL
			start_date_formatted = start_date.strftime("%Y-%m-%d %H:%M")
			end_date_formatted = end_date.strftime("%Y-%m-%d %H:%M")
			
			# Format it into "12Dec2024"
			human_readable_start_date = start_date.strftime("%d%b%Y").upper()
			formatted_start_date = start_date.strftime("%Y%m%d").upper()
			
			human_readable_end_date = end_date.strftime("%d%b%Y").upper()
			formated_end_date = end_date.strftime("%Y%m%d").upper()
			
			return (
				start_date,
				end_date,
				start_date_formatted,
				end_date_formatted,
				formatted_start_date,
				formated_end_date,
				human_readable_start_date,
				human_readable_end_date
				)
			
		else:
			raise ValueError("Date string format did not match expected pattern.")
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
	
	def parse_timestamp(self, extracted_data):
		for d in extracted_data:
			print(d)

		return extracted_data
	
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

	def update_drivers_json(self, d):
		pass