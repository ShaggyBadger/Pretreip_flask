import sys, os
from pathlib import Path
import pandas as pd
import re
from datetime import datetime
import console
# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Now you can import settings
import settings

'''
this module is responsible for processing in a spreadsheet, saving 
the data to the database, moving the file to the processed folder, and 
generating interpolated data if data is missing. 
'''

def mv_completed_file(dict_list, file_path):
	'''
	moves processed files out of
	unprocessed folder and into the
	processed folder
	'''
	
	processed_folder = Path(settings.PROCESSED_PATH)
	unprocessed_folder = Path(settings.UNPROCESSED_PATH)
	source_file = Path(file_path)
	
	sample_dict = dict_list[0]
	date = sample_dict['formated_start_date']
	
	new_file_name = f'speedGauge_{date}_driverCount_{len(dict_list)}.csv'
	
	target_path = processed_folder / new_file_name
	
	source_file.rename(target_path)

def parse_date_range(date_string):
	'''
	this is chatGPT wizardry. idk how 
	it works, but it does so dont mess
	with it
	'''
	
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
		
		return (start_date_formatted, end_date_formatted, formatted_start_date, formated_end_date,
		human_readable_start_date,
		human_readable_end_date)
		
	else:
		raise ValueError("Date string format did not match expected pattern.")

def extract_data(file):
	df = pd.read_csv(file)
	
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

def add_formated_date(dict_list, file):
	df = pd.read_csv(file)
	
	# Find the index of the row with '---'
	separator_index = df[df.iloc[:, 0] == '---'].index[0]
	
	# Date is 3ish rows below the
	# separator
	date_range = df.iloc[separator_index + 3, 0]
	
	# send the string to a cleaning
	# function
	cleaned_date = parse_date_range(date_range)
	for i in cleaned_date:
		print(i)
	
	# add formated dates to dictionary
	for dict in dict_list:
		dict['start_date'] = cleaned_date[0]
		dict['end_date'] = cleaned_date[1]
		dict['formated_start_date'] = cleaned_date[2]
		dict['formated_end_date'] = cleaned_date[3]
		dict['human_readable_start_date'] = cleaned_date[4]
		dict['human_readable_end_date'] = cleaned_date[5]

	return dict_list

def clean_data(dict_list):
	sanitized_dict_list = []
	
	# first, clean up ids
	for dict in dict_list:
		try:
			# see if the spreadsheet has driver_id column
			driver_id = dict['driver_id']
			
			# ensure id is an integer
			cleaned_id = int(float(str(driver_id)))
			
			# update dict with integer id
			dict['driver_id'] = cleaned_id
		
		except:
			# if no id, try to find one
			conn = settings.db_connection()
			c = conn.cursor()
			sql = f'SELECT driver_id FROM {settings.driverInfo} WHERE driver_name = ?'
			value = (dict['driver_name'],)

			c.execute(sql, value)
			result = c.fetchone()
			
			if result != None:
				dict['driver_id'] = result[0]
			else:
				dict['driver_id'] = None
			
			conn.close()
		

		sanitized_dict = {}
		
		# clean column names
		for key, value in dict.items():
			# Replace / and - with _
			sanitized_key = re.sub(r"[/-]", "_", key)
			sanitized_dict[sanitized_key] = value
			
			# put dictionary into list
		if sanitized_dict['driver_id'] != None:
			sanitized_dict_list.append(sanitized_dict)	

	return sanitized_dict_list

def update_db(dict_list):
	tbl = settings.speedGaugeData
	conn = settings.db_connection()
	c = conn.cursor()
	
	'''update driverInfo'''
	# organize dict info
	for dict in dict_list:
		driver_id = dict['driver_id']
		driver_name = dict['driver_name']
		
		# check db for driver_id
		sql = f'SELECT driver_id FROM {settings.driverInfo} WHERE driver_id = ?'
		value = (driver_id,)
		c.execute(sql, value)
		result = c.fetchone()
		
		# if id not in db, add it
		if result == None:
			sql = f'INSERT INTO {settings.driverInfo} (driver_name, driver_id) VALUES (?, ?)'
			values = (driver_name, driver_id)
			c.execute(sql, values)
			
	conn.commit()
	
	
	'''---update speedGaugeData---'''
	
	# check if dict column is in tbl
	sql = f'PRAGMA table_info({settings.speedGaugeData})'
	c.execute(sql)
	results = c.fetchall()
	col_names = []
	for result in results:
		col_names.append(result[1])
	sample_dict = dict_list[0]
	
	# update table if needed
	for col in sample_dict:
		if col not in col_names:
			valid_input = False
			while valid_input is False:
				console.clear()
				print(f'New column detected. Column name: {col}')
				message = (
					f'We have located a new column in the spreadsheet that is not in the database. '
					f'Please select which type of column it should be in the database...\n'
					f'1. TEXT\n'
					f'2. INTEGER\n'
					f'3. REAL\n'
					f'Enter your selection: '
					)
				user_input = input(message)
				input_options = {
					f'1': 'TEXT',
					f'2': 'INTEGER',
					f'3': 'REAL'
				}
				if str(user_input) in input_options:
					valid_input = True
			sql = (
				f'ALTER TABLE {settings.speedGaugeData} ADD COLUMN {col} {input_options[str(user_input)]}'
			)
			c.execute(sql)
			conn.commit()
	
	
	'''----insert row to table----'''
	
	for dict in dict_list:
		driver_id = dict['driver_id']
		start_date = dict['start_date']
		
		# check if this driver already has an entry for this date
		sql = f'SELECT * FROM {settings.speedGaugeData} WHERE driver_id = ? AND start_date = ?'
		values = (driver_id, start_date)
		
		c.execute(sql, values)
		result = c.fetchone()
		
		if result is None:	
			# build sql insertion
			columns = ', '.join(dict.keys())
			placeholders = ', '.join(['?' for _ in dict])
				
			sql = f'INSERT INTO {tbl} ({columns}) VALUES ({placeholders})'
			values = tuple(dict.values())
			c.execute(sql, values)
			
	conn.commit()
	conn.close()

def update_driverInfo2(file_name):
	'''
	go and sort through
	'''
	conn = settings.db_connection()
	c = conn.cursor()
	tbl = settings.driverInfo
	
	folder_path = Path(settings.PROCESSED_PATH)
	
	file_path = folder_path / file_name
	
	extracted_data = extract_data(file_path)
	
	valid_dicts = []
	invalid_dicts = []
	
	for dict in extracted_data:
		try:
			driver_name = dict['driver_name']
			driver_id = int(float(str(dict['driver_id'])))
			valid_dicts.append(dict)
		except:
			invalid_dicts.append(dict)
	
	entry_dicts = []
	for dict in valid_dicts:
		sql = f'SELECT driver_name FROM {tbl} WHERE driver_id = ?'
		value = (dict['driver_id'],)
		c.execute(sql, value)
		result = c.fetchone()
		if result == None:
			entry_dicts.append(dict)
	
	for dict in entry_dicts:
		driver_name = dict['driver_name']
		driver_id = int(float(str(dict['driver_id'])))
		sql = f'INSERT INTO {tbl} (driver_name, driver_id) VALUES (?, ?)'
		values = (driver_name, driver_id, )
		c.execute(sql, values)
	
	conn.commit()
	conn.close()
	return invalid_dicts

def get_driver_dates(driver_id):
	'''
	this returns a list of dates that 
	the driver has. it finrs the first
	date the drive has, then makes a
	filtered list for all the dates in
	the db from that point on
	
	returns the dates list so I can do
	math magic later with polynomial
	interpolation
	'''
	tbl = settings.driverInfo
	tbl2 = settings.speedGaugeData

	conn = settings.db_connection()
	c = conn.cursor()
	
	# get list of all dates in db
	sql = f'SELECT DISTINCT human_readable_start_date FROM {tbl2} ORDER BY formated_start_date ASC'
	c.execute(sql)
	date_list = [date[0] for date in c.fetchall()]

	# get list of dates for a driver
	sql = f'SELECT DISTINCT human_readable_start_date, percent_speeding FROM {tbl2} WHERE driver_id = ? ORDER BY formated_start_date'
	value = (driver_id,)
	c.execute(sql, value)
	driver_dates = [date[0] for date in c.fetchall()]
	
	# find oldest date for driver
	first_entry = driver_dates[0]
	
	# update dates_list to remove dates before drivers first entry
	start_index = date_list.index(first_entry)
	filtered_dates = date_list[start_index:]
			
	conn.close()
	return filtered_dates

def generate_missing_speed(driver_id, poly_degree=2):
	conn = settings.db_connection()
	c = conn.cursor()
	tbl1 = settings.driverInfo
	tbl2 = settings.speedGaugeData
	
	filtered_dates = get_driver_dates(driver_id)
	speeds = []
	for date in filtered_dates:
		sql = f'SELECT percent_speeding FROM {tbl2} WHERE driver_id = ? AND human_readable_start_date = ?'
		values = (driver_id, date)
		c.execute(sql, values)
		result = c.fetchone()
		if result != None:
			speeds.append(result[0])
		else:
			speeds.append(None)
	

	'''
	_____CHATGPT WIZARDRY_____
	     DO NOT MESS WITH
	'''
	
	from numpy.polynomial import Polynomial

	# Find indices of all missing values
	missing_indices = []
	for i, val in enumerate(speeds):
		if val is None:
			missing_indices.append(i)
	
	x = []
	y = []
	for i, val in enumerate(speeds):
		if val is not None:
			x.append(i)
			y.append(val)

	p = Polynomial.fit(x, y, deg=poly_degree)  # Fit a quadratic polynomial
	
	estimated_values = {}
	for index in missing_indices:
		estimated_values[index] = p(index)
	
	for i in estimated_values:
		date = filtered_dates[i]
		expected_speed = estimated_values[i]
		speeds[i] = expected_speed
	
	dict_list = []
	for index in missing_indices:
		date = filtered_dates[index]
		generated_speed = estimated_values[index]
		if generated_speed < 0:
			generated_speed = 0
		dict = {
			'date': date,
			'percent_speeding': generated_speed,
			'driver_id': driver_id
		}
		dict_list.append(dict)
		
	conn.close()
	return dict_list
	
def update_missing_speeds(print_errors=False):
	conn = settings.db_connection()
	c = conn.cursor()
	tbl1 = settings.driverInfo
	tbl2 = settings.speedGaugeData
	driver_id_list = []
	
	# get list of drivers
	sql = f'SELECT DISTINCT driver_id FROM {tbl1}'
	c.execute(sql)
	results = c.fetchall()
	for result in results:
		driver_id = result[0]
		driver_id_list.append(driver_id)
	
	# get interpolation data for drivers
	counter = 0
	for driver_id in driver_id_list:
		sql = f'SELECT driver_name FROM {tbl2} WHERE driver_id = ?'
		value = (driver_id,)
		c.execute(sql, value)
		result = c.fetchone()
		driver_name = result[0]
		
		try:
			dict_list = generate_missing_speed(driver_id)
		except Exception as e:
			if print_errors is True:
				print(f'Error processing driver {driver_id}: {e}')
		
		try:
			for dict in dict_list:	
				date = dict['date']
				sql = f'SELECT start_date, end_date, formated_start_date, formated_end_date, human_readable_start_date, human_readable_end_date FROM {tbl2} WHERE human_readable_start_date = ?'
				value = (date,)
				c.execute(sql, value)
				result = c.fetchone()
				
				if result is None:
					print(f'Skipping insertion for driver_id {driver_id} and date {date}: No matching data')
					continue
				
				percent_speeding = round(dict['percent_speeding'], 2)
				driver_id = dict['driver_id']
				start_date = result[0]
				end_date = result[1]
				formated_start_date = result[2]
				formated_end_date = result[3]
				human_readable_start_date = result[4]
				human_readable_end_date = result[5]
						
				sql = f'INSERT INTO {tbl2} (driver_id, driver_name, percent_speeding, start_date, end_date, formated_start_date, formated_end_date, human_readable_start_date, human_readable_end_date, percent_speeding_source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
				values = (
					driver_id,
					driver_name,
					percent_speeding,
					start_date,
					end_date,
					formated_start_date,
					formated_end_date,
					human_readable_start_date,
					human_readable_end_date,
					'generated'
					)
				
				c.execute(sql, values)
				
				if counter % 100 ==0:
					print(f'Insering values...')
					for i in values:
						print(i)
					print('***************\n')
				counter += 1
		except:
			pass
	conn.commit()
	print(f'Entries built using interpolated data: {counter}')
	
	conn.close()
	
def interpolated_gen_report():
	conn = settings.db_connection()
	c = conn.cursor()
	
	sql = f'SELECT * FROM {settings.speedGaugeData} WHERE percent_speeding_source = ?'
	
	value = ('generated',)
	c.execute(sql, value)
	results = c.fetchall()
	print(f'number of db entries that have a generated percent speeding: {len(results)}')

	sql = f'SELECT * FROM {settings.speedGaugeData} WHERE driver_id IS NULL'
	c.execute(sql)
	results = c.fetchall()
	print(f'NUM OF NULL DRIVERS: {len(results)}')
	
	print('Deleting any entries with NULL values...\n')
	sql = f'DELETE FROM {settings.speedGaugeData} WHERE driver_name IS NULL'
	c.execute(sql)
	conn.commit()
	
	sql = f'SELECT * FROM {settings.speedGaugeData} WHERE driver_id IS NULL'
	c.execute(sql)
	results = c.fetchall()
	print(f'NUM OF NULL DRIVERS: {len(results)}')

	conn.close()

def processing_summary():
	conn = settings.db_connection()
	c = conn.cursor()
	tbl1 = settings.driverInfo
	tbl2 = settings.speedGaugeData
	
	# retreive latest date from db
	sql = f'SELECT MAX(start_date) FROM {tbl2}'
	c.execute(sql)
	result = c.fetchone()
	max_date = result[0]
	max_date_printout = f'\nProcessing summary for week starting {max_date}\n------------------\n'
	
	# find how many insertions for latest week
	sql = f'SELECT * FROM {tbl2} WHERE start_date = ?'
	value = (max_date,)
	c.execute(sql, value)
	results = c.fetchall()
	insertion_count_printout = f'Total number of insertions: {len(results)}\n'

	# find how many insertions were interpolated
	sql = f'SELECT * FROM {tbl2} WHERE start_date = ? AND percent_speeding_source = ?'
	value = (max_date, 'generated')
	c.execute(sql, value)
	results = c.fetchall()
	interpolated_insertions_printout = f'Total number of interpolated insertions: {len(results)}'

	return max_date_printout + insertion_count_printout + interpolated_insertions_printout

def main(initializer=False):
	'''
	initialize is set to true if this is a clean build from clones repo. 
	This is part of the intialize.py file
	'''
	folder_path = settings.UNPROCESSED_PATH

	for file in folder_path.iterdir():
		if file.is_file():
			# extract data from spreadsheet
			extracted_data = extract_data(file)
			
			#clean data
			cleaned_data = clean_data(extracted_data)
			
			# add formates dates to data
			cleaner_data = add_formated_date(cleaned_data, file)
			
			# update database
			update_db(cleaner_data)
			
			# move file to processed folder
			mv_completed_file(cleaner_data, file)
			
			# search for and update any missing speeds
			if initializer is False:
				update_missing_speeds()
				interpolated_gen_report()
			
			# print out a summary
			summary = processing_summary()
			print(summary)
		


if __name__ == '__main__':
	update_missing_speeds()
	interpolated_gen_report()
