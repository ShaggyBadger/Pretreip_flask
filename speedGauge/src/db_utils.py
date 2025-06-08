import sys
import os
import sqlite3
import console
import statistics
import math

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Now you can import settings
import settings
def db_connection():
	# returns a db connection
	dbName = settings.DB_PATH
	conn = sqlite3.connect(dbName)
	return conn

def build_driver_data_json():
	'''
	builds a json file with driver first and last name as well as driver id. puts the file in the data directory
	'''
	conn = db_connection()
	c = conn.cursor()
	driver_dict_list = []
	
	sql = f'''
	SELECT DISTINCT 
		driver_name,
		driver_id
	FROM {settings.driverInfo}
	'''
	c.execute(sql)
	result = c.fetchall()
	for i in result:
		name = i[0]
		driver_id = i[1]
		
		parts = name.strip().split()
		fname = parts[0]
		lname = parts[-1]
		
		driver_dict = {
			'driver_id': driver_id,
			'first_name': fname,
			'last_name': lname
		}
		
		driver_dict_list.append(driver_dict)
	
	conn.close()
	
	import json
	file_path = settings.DATA_PATH / 'drivers.json'
	with open(file_path, 'w') as f:
		json.dump(driver_dict_list, f, indent=2)

def gather_locations(center=settings.km2_coords, max_distance=50):
	conn = db_connection()
	c = conn.cursor()
	
	sql = f'SELECT url, location FROM {settings.speedGaugeData}'
	c.execute(sql)
	results = c.fetchall()
	
	filtered_results = [
		result for result in results
		if result[0] not in (None, '-')
		and result[1] not in (None, '-')
		]
	
	conn.close()
	
	valid_locations = []
	
	for result in filtered_results:
		url = result[0]
		location = result[1]
		
		url_coords = settings.extract_coordinates(url)
		
		distance_from_center = settings.haversine(url_coords[0], url_coords[1], center[0], center[1])
		
		if distance_from_center <= max_distance:
			final_result = [
				i for i in result
				]
			final_result.append(distance_from_center)
			final_result.append(url_coords)
			valid_locations.append(final_result)
	
	sorted_locations = sorted(valid_locations, key=lambda x: x[2])
	
	return sorted_locations

def find_names_and_ids(rtm='chris'):
	conn = settings.db_connection()
	c = conn.cursor()
	
	sql = f'SELECT driver_name, driver_id FROM {settings.driverInfo} WHERE rtm = ?'
	value = (rtm,)
	c.execute(sql, value)
	results = c.fetchall()
	intel_dict = {}
	for result in results:
		intel_dict[result[1]] = result[0]
	
	
	for i in intel_dict:
		print(intel_dict[i], i)
	
	conn.close()

def store_json_data(stats_json, plt_paths_json, rtm, start_date):
	conn = settings.db_connection()
	c = conn.cursor()
	
	sql = f'SELECT id FROM {settings.analysisStorage} WHERE start_date = ?'
	value = (start_date,)
	c.execute(sql, value)
	result = c.fetchone()
	
	if result is None:
		# make new entry
		sql = f'INSERT INTO {settings.analysisStorage} (start_date, rtm, stats, plt_paths) VALUES (?, ?, ?, ?)'
		values = (start_date, rtm, stats_json, plt_paths_json)
		c.execute(sql, values)
		print('Saving new json data to db')
	else:
		# override existing entry
		id = result[0]
		sql = f'UPDATE {settings.analysisStorage} SET rtm = ?, stats = ?, plt_paths = ? WHERE id = ?'
		values = (rtm, stats_json, plt_paths_json, result[0])
		c.execute(sql, values)
		print('Overriding exsisting json data in the db with new json data')
	
	conn.commit()
	conn.close()

def build_analysisStorage_tbl():
	'''creates the analysisStorage table used for storing analysis and plt_paths json files'''
	conn = settings.db_connection()
	c = conn.cursor()
	
	# Create tables if they don't already exist
	analysisStorage_tblName = settings.analysisStorage
	
	analysisStorage_columns = ', '.join([f'{col_name} {col_type}' for col_name, col_type in settings.analysisStorageTbl_column_info.items()])
	
	# build table
	sql = f'CREATE TABLE IF NOT EXISTS {analysisStorage_tblName} ({analysisStorage_columns})'
	c.execute(sql)
	
	# commit and close
	conn.commit()
	conn.close()
	print('analysisStorage table created successfully')

def build_imgStorage_tbl():
	'''creates the imgStorage table used for storing plots and stuff'''
	conn = settings.db_connection()
	c = conn.cursor()
	
	# Create tables if they don't already exist
	imgStorage_tblName = settings.imgStorage
	
	imgStorage_columns = ', '.join([f'{col_name} {col_type}' for col_name, col_type in settings.imgStorageTbl_column_info.items()])
	
	# build table
	sql = f'CREATE TABLE IF NOT EXISTS {imgStorage_tblName} ({imgStorage_columns})'
	c.execute(sql)
	
	# commit and close
	conn.commit()
	conn.close()

def get_manager(driver_id):
	conn = settings.db_connection()
	c = conn.cursor()
	
	sql = f'SELECT rtm FROM {settings.driverInfo} WHERE driver_id = ?'
	value = (driver_id,)
	c.execute(sql, value)
	result = c.fetchone()
	conn.close()
	
	if result != None:
		manager = result[0]
		return manager
	else:
		return None

def get_max_date():
	'''
	returns the highest start_date in
	the database
	'''
	conn = settings.db_connection()
	
	c = conn.cursor()
	sql = f'SELECT MAX (start_date) FROM {settings.speedGaugeData}'
	c.execute(sql)
	result = c.fetchone()[0]
	
	conn.close()
	return result

def get_all_dates():
	'''
	returns list of each start_date in the database in ascending order -
	that is, oldest date is index 0
	'''
	date_list = []
	
	conn = settings.db_connection()
	c = conn.cursor()
	
	sql = f'SELECT DISTINCT start_date FROM {settings.speedGaugeData} ORDER BY start_date ASC'
	
	c.execute(sql)
	results = c.fetchall()
	for date in results:
		date_list.append(date[0])
		
	conn.close()
	return date_list

def gather_driver_ids(rtm='chris'):
	'''
	returns all the driver numbers for
	a given rtm 
	
	if rtm = company, then returns ALL 
	driver numbers
	'''
	
	id_list = []
	
	conn = settings.db_connection()
	c = conn.cursor()
	
	if rtm != 'company':
		sql = f'SELECT driver_id FROM {settings.driverInfo} WHERE rtm = ?'
		value = (rtm,)
		
		c.execute(sql, value)
		results = c.fetchall()
		
		for result in results:
			id_list.append(result[0])
	
	else:
		sql = f'SELECT driver_id FROM {settings.driverInfo}'
		
		c.execute(sql)
		results = c.fetchall()
		
		for result in results:
			id_list.append(result[0])
	
	conn.close()
	return id_list

def gather_driver_data(id_list, date):
	'''
	takes in a list of driver_ids and returns a list full of dictionaries
	
	dictionary keys:
		driver_id
		driver_name
		percent_speeding
	
	this is limited to the given date in the database
	
	argumnt 1 is id_list, argument2 
	'''
	
	print(f'Gathering driver data for {date}....')
	
	tbl = settings.speedGaugeData
	data_packets = []
	#max_date = get_max_date()
	conn = settings.db_connection()
	c = conn.cursor()
	
	for driver_id in id_list:
		sql = f'SELECT driver_name, percent_speeding, distance_driven FROM {tbl} where driver_id = ? AND start_date = ?'
		values = (driver_id, date)
		
		c.execute(sql, values)
		result = c.fetchone()
		
		if result != None:
			driver_name = result[0]
			percent_speeding = result[1]
			distance_driven = result[2]
			
			data_packet = {
				'driver_id': driver_id,
				'percent_speeding': percent_speeding,
				'driver_name': driver_name,
				'distance_driven': distance_driven
			}
			
			data_packets.append(data_packet)

	conn.close()
	return data_packets

def gather_historical_driver_data(id_list):
	'''
	takes in a list of driver_id and
	returns mean and avg for each date
	in the db
	
	returns dict with these keys:
		date
		mean
		median
	
	use this to make line plot showing
	historical trends.
	
	there should be one dictionary per
	date
	'''
	print('Gathering historical driver data...')
	
	tbl = settings.speedGaugeData
	stats = []
	date_list = get_all_dates()
	
	conn = settings.db_connection()
	c = conn.cursor()
	
	for date in date_list:
		speed_list = []
		
		for driver_id in id_list:
			sql = f'SELECT percent_speeding FROM {tbl} WHERE start_date = ? AND driver_id = ?'
			values = (date, driver_id)
			
			c.execute(sql, values)
			results = c.fetchone()
			
			if results != None:
				percent_speeding = results[0]
				
				speed_list.append(percent_speeding)

		mean = statistics.mean(speed_list)
		median = statistics.median(speed_list)
		
		stats_dict = {
			'date': date,
			'mean': mean,
			'median': median
		}
		
		stats.append(stats_dict)
	
	conn.close()
	return stats

def print_driver_info(driver_id):
	conn = settings.db_connection()
	c = conn.cursor()
	tbl = settings.driverInfo
	
	sql = f'SELECT * FROM {tbl} WHERE driver_id = ?'
	value = (driver_id,)
	c.execute(sql, value)

	result = c.fetchone()
	for i in result:
		print(i)
	
def idr_driver_data(driver_id=30150643):
	'''
	Retrieves historical driving data for a specific driver from the database.
	
	This function fetches the earliest recorded date for the given driver, retrieves 
	all distinct dates from that point onward, extracts column names from the table, 
	and compiles the driver's data into a list of dictionaries.
	
	Args:
		driver_id (int, optional): The ID of the driver to retrieve data for. 
		
		Defaults to 30150643.
	
	Returns:
		list[dict]: A list of dictionaries where each dictionary represents a row of 
		driver data, with column names as keys.
	
	Notes:
		- Connects to the database using `settings.db_connection()`.
		- Queries the earliest `start_date` for the driver.
		- Retrieves a sorted list of unique `start_date` values from that point onward.
		- Extracts column names dynamically using `PRAGMA table_info`.
		- Fetches all records for the driver, ordered by `start_date`.
		- Converts query results into dictionaries using column names as keys.
	'''
	conn = settings.db_connection()
	c = conn.cursor()
	
	# get earliest date for driver
	sql = f'SELECT MIN(start_date) FROM {settings.speedGaugeData} WHERE driver_id = ?'
	value = (driver_id,)
	c.execute(sql, value)
	result = c.fetchone()
	
	first_date = result[0]
	
	# get list of all dates from earliest onward
	sql = f'SELECT DISTINCT start_date FROM {settings.speedGaugeData} WHERE start_date >= ? ORDER BY start_date ASC'
	value = (first_date,)
	c.execute(sql, value)
	results = c.fetchall()
	
	date_list = [result[0] for result in results]
	
	# get column names
	sql = f'PRAGMA table_info({settings.speedGaugeData})'
	c.execute(sql)
	results = c.fetchall()
	column_names = [result[1] for result in results]
	
	# build query
	sql = f'SELECT * FROM {settings.speedGaugeData} WHERE driver_id = ? ORDER BY start_date ASC'
	value = (driver_id,)
	c.execute(sql, value)
	results = c.fetchall()
	
	
	
	dict_list = [
		dict(zip(column_names, result)) for result in results
		]
	
	conn.close()
	
	return dict_list

def verify_driver_id(driver_id):
	'''
	Verify if a given driver ID exists in the database.
	
	Args:
		driver_id (int): The ID of the driver to check.
	
	Returns:
		bool: True if the driver ID exists, False otherwise.
	'''

	conn = settings.db_connection()
	c = conn.cursor()
	
	sql = f'SELECT driver_name FROM {settings.speedGaugeData} WHERE driver_id = ?'
	value = (driver_id,)
	c.execute(sql, value)
	result = c.fetchone()
	conn.close()
	
	if result == None:
		return False
	
	else:
		return True

if __name__ == '__main__':
	#build_analysisStorage_tbl()
	#gather_locations()
	#idr_driver_data()
	build_driver_data_json()
