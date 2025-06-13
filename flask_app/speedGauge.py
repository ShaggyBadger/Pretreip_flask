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
			# build list  of dictionaries. each dict one row of csv
			extracted_data = self.extract_data(csv_file)

			# build date info from the csv and attach it to the dictionary for each row
			date_info = self.extract_date(csv_file)
			for driver_dict in extracted_data:
				# insert the dates
				driver_dict['start_date'] = date_info[0]
				driver_dict['end_date'] = date_info[1]

				# fix the names. Isolate the first and last name, and attach that  to the dictionary
				parsed_names = self.parse_names(driver_dict['driver_name'])
				driver_dict['first_name'] = parsed_names[0]
				driver_dict['last_name'] = parsed_names[1]

				# if driver_dict is missing driver_number, run this to find it and add driver_num to dict
				if driver_dict['driver_id'] is None:
					driver_num = self.locate_missing_driver_number(driver_dict)
					driver_dict['driver_id'] = driver_num

				# add coords of url
				driver_dict['url_coords'] = self.get_lat_long(driver_dict['url'])

				# add raw_json of all this stuff to the dict
				driver_dict_json_string = json.dumps(driver_dict)
				driver_dict['raw_json'] = driver_dict_json_string

	def parse_names(self, name_str):
		'''This takes string with full name and returns just first and last name'''
		# strip extra white spaces
		cleaned_name = name_str.strip()

		# break name into parts
		name_parts = cleaned_name.split()

		# Handle edge cases
		if not name_parts:
			return None, None  # Empty string or only whitespace
		elif len(name_parts) == 1:
			return name_parts[0], None # Only one name provided
		else:
			first_name = name_parts[0]
			last_name = name_parts[-1]
			return first_name, last_name
	def get_lat_long(self, url):
		'''
		Extracts latitude and longitude coordinates from a given URL string.
		
		The function searches for latitude (`la=`) and longitude (`lo=`) parameters 
		in the URL and returns them as a tuple of floats. If no match is found, it returns None.
		
		Parameters:
			url (str): The URL containing latitude and longitude values.
		
		Returns:
			tuple[float, float] | None: A tuple (latitude, longitude) if found, otherwise None.
		
		Example:
			>>> get_lat_long("https://example.com?la=35.827877&lo=-80.860069&")
			
			(35.827877, -80.860069
		'''
		pattern = r'la=(-?\d+\.\d+)&lo=(-?\d+\.\d+)&'
		match = re.search(pattern, url)
		
		if match:
			lat = float(match.group(1))
			long = float(match.group(2))
			return lat, long
		
		else:
			return None
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
		This method locates the date in the csv, converts it to datetime object and then makes it a string
		in ISO format so it can easily be converted back into a datetime object when I pull it out of the
		database.
		'''
		df = pd.read_csv(csv_file)
		# Find the index of the row with '---'
		separator_index = df[df.iloc[:, 0] == '---'].index[0]
	
		# Date is 3ish rows below the
		# separator
		date_range = df.iloc[separator_index + 3, 0]
		
		# Define a regex to capture the two date components
		date_pattern = r"(\w+, \w+ \d{1,2}, \d{4}, \d{2}:\d{2})"
		matches = re.findall(date_pattern, date_range)
		
		if len(matches) == 2:
			# Parse the matched date strings
			start_date_str, end_date_str = matches
			
			# Define the format matching the date string
			date_format = "%A, %B %d, %Y, %H:%M"
			
			# Convert to datetime objects
			start_date_obj = datetime.strptime(start_date_str, date_format)
			end_date_obj = datetime.strptime(end_date_str, date_format)
			start_date = start_date_obj.date().isoformat()
			end_date = end_date_obj.date().isoformat()

			return start_date, end_date, start_date_str, end_date_str
			
		else:
			raise ValueError("Date string format did not match expected pattern.")
	def extract_data(self, csv_file):
		'''Pulls the data from the csv. Takes each row and makes a dictionary, then stores the dictionaries
		in a list. The list is what gets returned by this method'''
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


		return extracted_data
	def check_tbl_exists(self, tbl_name):
		'''Might not need this method. Returns true if a table exists already'''
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
		'''easy way to establish a db connection inside this class'''
		conn = sqlite3.connect(settings.db_name)
		
		return conn
	def update_drivers_json(self, d):
		'''i have no idea what we are doing here. Probably updating the json file with any new driver info we
		might find from week to week'''
		pass
	def locate_missing_driver_number(self, driver_dict):
		'''search through the driver_info table and locate driver number based on driver_name?'''
		first_name = driver_dict['first_name']
		last_name = driver_dict['last_name']

		drivers_json = settings.DATABASE_DIR / 'drivers.json'
		try:
			with open(drivers_json, 'r', encoding='utf-8') as file:
				drivers_list = json.load(file)
				for driver  in drivers_list:
					if driver['first_name'].lower() == first_name.lower() and driver['last_name'].lower() == last_name.lower():
						driver_number = driver['driver_id']
						return driver_number
		except:
			print('Unable to get this driver info for some reason')
			return None
