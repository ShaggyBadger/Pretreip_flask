import statistics
import numpy as np
import sys
import os
import sqlite3
import console
import math
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Now you can import settings
import settings






def db_connection():
	# returns a connection
	dbName = settings.DB_PATH
	conn = sqlite3.connect(dbName)

	return conn
















def get_max_date():
	'''
	returns the highest start_date in
	the database
	'''
	
	tbl = 'speedGaugeData'
	conn = db_connection()
	
	c = conn.cursor()
	sql = f'SELECT MAX (start_date) FROM {tbl}'
	c.execute(sql)
	result = c.fetchone()[0]
	
	conn.close()
	
	return result















	
def validate_driver_num(driver_num):
	'''
	checks if a given driver number 
	exists in the database
	'''
	conn = db_connection()
	c = conn.cursor()
	
	sql = f'SELECT * FROM driverInfo WHERE driver_id = ?'
	value = (driver_num,)
	c.execute(sql, value)
	result = c.fetchone()
	conn.close()
	
	if result == None:
		input('Driver number is not in the database. Please enter to try again...')
		return False
	
	else:
		print(f'Initialize processing for {result[1]}...\n')
		return True














def get_all_dates(driver='none'):
	'''
	returns list of each start_date in
	the database
	'''
	
	tbl = 'speedGaugeData'
	date_list = []
	
	conn = db_connection()
	c = conn.cursor()
	
	if driver == 'none':
		sql = f'SELECT DISTINCT start_date FROM {tbl} ORDER BY start_date ASC'
		c.execute(sql)
	else:
		sql = f'SELECT DISTINCT start_date FROM {tbl} WHERE driver_id = ? ORDER BY start_date ASC'
		value = (driver,)
		c.execute(sql, value)
		
	results = c.fetchall()
	for date in results:
		date_list.append(date[0])
		
	conn.close()
	return date_list










def collect_all_speeds(rtm='chris'):
	conn = db_connection()
	c = conn.cursor()
	tbl = 'speedGaugeData'
	dates = get_all_dates()
	
	rtm_driver_ids = []
	company_driver_ids = []
	rtm_data_list = []
	company_data_list = []
	rtm_current_speed_list = []
	rtm_previous_speed_list = []
	company_current_speed_list = []
	company_previous_speed_list = []
	
	# gather rtm driver ids
	sql = f'SELECT DISTINCT driver_id FROM driverInfo WHERE rtm = ?'
	value = (rtm,)
	c.execute(sql, value)
	results = c.fetchall()
	for i in results:
		rtm_driver_ids.append(i[0])
	
	# gather company-wide driver ids
	sql = f'SELECT DISTINCT driver_id FROM driverInfo'
	c.execute(sql)
	results = c.fetchall()
	for i in results:
		company_driver_ids.append(i[0])
	
	# build data for rtm
	for date in dates:
		date_info = {}
		spd_list = []

		for driver in rtm_driver_ids:
			sql = f'SELECT percent_speeding FROM {tbl} WHERE start_date = ? AND driver_id = ?'
			values = (date, driver)
			c.execute(sql, values)
			result = c.fetchone()

			try:
				spd_list.append(result[0])
			except:
				pass
		
		if date == dates[-1]:
			rtm_current_speed_list.extend(spd_list)
		
		if date == dates[-2]:
			try:
				rtm_previous_speed_list.extend(spd_list)
			except:
				print(result, date)

		date_info['date'] = date
		date_info['speed_list'] = spd_list
		rtm_data_list.append(date_info)
	
	# build data for company
	for date in dates:
		date_info = {}
		spd_list = []

		for driver in company_driver_ids:
			sql = f'SELECT percent_speeding FROM {tbl} WHERE start_date = ? AND driver_id = ?'
			values = (date, driver)
			c.execute(sql, values)
			result = c.fetchone()

			try:
				spd_list.append(result[0])
			except:
				pass
			
			if date == dates[-1]:
				company_current_speed_list.extend(spd_list)
			
			if date == dates[-2]:
				company_previous_speed_list.extend(spd_list)

		date_info['date'] = spd_list
		company_data_list.append(date_info)
	
	data_package = {
		'rtm_speed_lists': rtm_data_list,
		'company_speed_lists': company_data_list,
		'rtm_current_speed_list': rtm_current_speed_list,
		'rtm_previous_speed_list': rtm_previous_speed_list,
		'company_current_speed_list': company_current_speed_list,
		'company_previous_speed_list': company_previous_speed_list
	}
	
	return data_package
	











def build_data_set(driver_num):
	conn = db_connection()
	c = conn.cursor()
	all_dates = get_all_dates()
	
	dict_list = []
	for date in all_dates:
		col_names = []

		sql = f'SELECT * FROM speedGaugeData WHERE driver_id = ? AND start_date = ?'
		values = (driver_num, date)
		
		c.execute(sql,values)
		results = c.fetchone()
		
		for col in c.description:
			col_names.append(col[0])
		
		try:
			row_dict = dict(zip(col_names, results))
		
			dict_list.append(row_dict)
		except :
			print(f'Error loading data from {date}. The driver likely took that week off. This message comes from the build_data_set function in the individualizedDriverReport file')
			print('--------\n')
			input('Press enter to continue....')
			print('\n\n')

	conn.close()
	
	return dict_list
		







def determine_change(base_value, new_value):
	'''
	use to determine how much the new 
	value differs from the base value
	'''
	# determine change from median
	if base_value == 0:
		percent_change = ((new_value - base_value) / (base_value + 1)) * 100
	else:
		percent_change = ((new_value - base_value) / base_value) * 100
	
	return percent_change















def analyze_data(data_set, driver_id, debug=False):
	speed_list = []
	all_speeds = collect_all_speeds()

	location_list = []
	date_set = get_all_dates()
	
	# organize dates
	latest_date = date_set[-1]
	second_latest_date = date_set[-2]
	latest_dict = None
	second_latest_dict = None
	
	rtm_historical_speeds = all_speeds['rtm_speed_lists']

	company_historical_speeds = all_speeds['company_speed_lists']
	
	# isolate dicts
	for dict in data_set:
		location_list.append(dict['location'])
		speed_list.append(dict['percent_speeding'])
		
		if dict['start_date'] == latest_date:
			latest_dict = dict
	for dict in data_set:
		if dict['start_date'] == second_latest_date:
			second_latest_dict = dict

	latest_speeding = latest_dict['percent_speeding']
	last_week_speeding = second_latest_dict['percent_speeding']

	speed_list.sort()
	
	# statistic stuff
	mean = statistics.mean(speed_list)
	median = statistics.median(speed_list)
	stdev = statistics.stdev(speed_list)
	
	change_from_avg =  latest_speeding - mean
	change_from_median = latest_speeding - median
	
	company_current_avg_percent_speeding = statistics.mean(all_speeds['company_current_speed_list'])
	company_previous_avg_percent_speeding = statistics.mean(all_speeds['company_previous_speed_list'])
	rtm_current_avg_percent_speeding = statistics.mean(all_speeds['rtm_current_speed_list'])
	rtm_previous_avg_percent_speeding = statistics.mean(all_speeds['rtm_previous_speed_list'])
	
	# determine change from median
	median_change = determine_change(median, latest_speeding)
	
	# determine change from average
	avg_change = determine_change(mean, latest_speeding)
		
	# determine percentage change from
	# last week
	percent_speed_change = determine_change(last_week_speeding, latest_speeding)
	
	week_speed_change = latest_dict['percent_speeding'] - second_latest_dict['percent_speeding']
	
	percent_week_change = determine_change(second_latest_dict['percent_speeding'], latest_dict['percent_speeding'])
	
	abs_change_driver_to_market = latest_speeding - rtm_current_avg_percent_speeding
	
	percent_change_driver_to_market = determine_change(rtm_current_avg_percent_speeding, latest_speeding)
	
	abs_change_driver_to_company = latest_speeding - company_current_avg_percent_speeding
	
	percent_change_driver_to_company = determine_change(company_current_avg_percent_speeding, latest_speeding)
	
	if stdev != 0:
		stdev_from_mean = abs(round((latest_speeding - mean) / stdev))
	
	else:
		stdev_from_mean = 1
	
	# get driver name
	conn = db_connection()
	c = conn.cursor()
	sql = f'SELECT driverName FROM driverInfo WHERE driver_id = ?'
	value = (driver_id,)
	c.execute(sql, value)
	result = c.fetchone()
	driver_name = result[0]
	conn.close()

	# organize info for return
	stats = {
		'date_set': date_set,
		'driver_name': driver_name,
		'driver_id': driver_id,
		'latest_percent_speeding': latest_speeding,
		'previous_percent_speeding': second_latest_dict['percent_speeding'],
		'abs_change_from_last_week': week_speed_change,
		'percent_change_from_last_week': percent_week_change,
		'percent_change_from_last_week': percent_speed_change,
		'company_current_avg': company_current_avg_percent_speeding,
		'company_previous_avg': company_previous_avg_percent_speeding,
		'rtm_current_avg': rtm_current_avg_percent_speeding,
		'rtm_previous_avg': rtm_previous_avg_percent_speeding,
		'avg': mean,
		'abs_driver_to_market': abs_change_driver_to_market,
		'percent_driver_to_market': percent_change_driver_to_market,
		'abs_driver_to_company': abs_change_driver_to_company,
		'percent_driver_to_company': percent_change_driver_to_company,
		'median': median,
		'stdev': stdev,
		'stdev_from_mean': stdev_from_mean,
		'abs_avg_change': change_from_avg,
		'percent_change_from_avg': avg_change,
		'abs_median_change': change_from_median,
		'percent_change_from_median': median_change
	}
	
	# dict to hold lists of info for
	# report tables
	data_sets = {
		'location_list': location_list,
		'driver_speed_list': speed_list,
		'company_current_avg_speed_list': company_current_avg_percent_speeding,
		'rtm_current_avg_speed_lisr': rtm_current_avg_percent_speeding
	}
	
	analysis_packet = {
		'stats': stats,
		'data_sets': data_sets
	}
	
	return analysis_packet
	




def generate_line_chart(dates, driver_speeds, rtm_speeds, company_speeds):
	rtm_label = 'RTM Average Perfent Speeding'
	company_label = 'Company Average Percent Speeding'
	driver_label = 'Driver Percent Speeding'
	x_label = 'Date'
	y_label = f'Percent Speeding'
	title = f'Historical distribution of Percent Speeding'
	
	
	# Convert string dates to datetime objects
	dates2 = [datetime.strptime(date, '%Y-%m-%d %H:%M') for date in dates]
		
	plt.figure(constrained_layout=True)
	plt.plot(dates2, rtm_speeds, label=rtm_label, color='Blue', linestyle='-')
	
	plt.plot(dates2, company_speeds, label=company_label, color='green', linestyle='-')
	
	plt.plot(dates2, driver_speeds, label=driver_label, color='red', linestyle='-')
	
	# Set major locator to one tick per month
	plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
	
	# Format the date labels to show the month and year (e.g., Jan 2024)
	plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
	
	# Rotate the labels for readability
	plt.xticks(rotation=45)
	
	# Automatically adjust layout to avoid clipping
	#plt.tight_layout()
	#plt.subplots_adjust(bottom=0.15, left=0.15)  # Adjust bottom and left margins
	
	plt.xlabel(x_label)
	plt.ylabel(y_label)
	plt.title(title)
	plt.legend()
	
	return plt

















def gen_histogram(speed_list, driver_speed, numBins=15):
	x_label = 'Speeding Percentage'
	y_label = 'Number Of Drivers'
	title = 'Distribution Of Speeding Percentages For The Week'
	
	plt.figure()
	n, bins, patches = plt.hist(speed_list, bins=numBins, edgecolor='black', color='blue', label='Rtm Stats')
	
	# Find the index of the bin containing the driver's speeding percentage
	bin_index = np.digitize(driver_speed, bins) - 1  # `np.digitize` returns 1-based index, so subtract 1 for 0-based
	
	# Highlight the driver's bin
	if 0 <= bin_index < len(patches):
		# Ensure the index is valid
		patches[bin_index].set_facecolor('#ff3535')
		patches[bin_index].set_edgecolor('black')
		patches[bin_index].set_linewidth(2)
		patches[bin_index].set_hatch('x')
	
	plt.xlabel(x_label)
	plt.ylabel(y_label)
	plt.title(title)
	
	return plt











def save_plt(processing_data, debug=False):
	plt = processing_data['plt']
	date = processing_data['current_date']
	driver_name = processing_data['driver_name']
	driver_id = processing_data['driver_id']
	plt_type = processing_data['plt_type']
	
	# Parse date into a datetime object
	date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M")

	# Format it into "12Dec2024"
	formatted_date = date_obj.strftime("%d%b%Y").upper()
	
	# build path
	BASE_DIR = Path(settings.BASE_DIR)
	report_dir = BASE_DIR / 'images' / 'IDR' / formatted_date
	# IDR = individual driver report
	
	
	if report_dir.exists():
		if debug is True:
			print(f'The directory {report_dir} already exists. Continuing on...')
	else:
		report_dir.mkdir(parents=True, exist_ok=True)
		
		if debug is True:
			print(f'The directory {report_dir} does not exist. Creating it now...')
			print(f'Directory {report_dir} has been created')
	
	# Build file path for saving the plot
	file_name = f"{driver_name.split()[0]}_{driver_id}_{plt_type}_{formatted_date}.png"
	file_path = report_dir / file_name
	
	# Save the plot
	plt.savefig(file_path)
	if debug is True:
		print(f"Plot saved at: {file_path}")
	
	return file_path












def build_graphs(driver_id, driver_avg):
	print('\n-----Building Graphs-----\n')
	target_driver = driver_id
	tbl = 'speedGaugeData'
	driver_historic_speeds = []
	rtm_historic_avg_speeds = []
	company_historic_avg_speeds = []
	rtm_current_speeds = []
	company_current_speeds = []
	
	rtm_ids = []
	company_ids = []
	plt_paths = {}
	
	conn = db_connection()
	c = conn.cursor()
	dates = get_all_dates()
	
	sql = f'SELECT driverName FROM driverInfo WHERE driver_id = ?'
	value = (driver_id,)
	c.execute(sql, value)
	result = c.fetchone()
	driver_name = result[0]
	
	# get driver rtm
	sql = f'SELECT rtm FROM driverInfo WHERE driver_id = ?'
	value = (driver_id,)
	c.execute(sql, value)
	result = c.fetchone()
	if result == None:
		rtm = 'chris'
	else:
		rtm = result[0]
	
	# get rtm ids
	sql = f'SELECT DISTINCT driver_id FROM driverInfo WHERE rtm = ?'
	value = (rtm,)
	c.execute(sql, value)
	results = c.fetchall()
	for result in results:
		rtm_ids.append(result[0])
	
	# get company ids
	sql = f'SELECT DISTINCT driver_id FROM driverInfo'
	c.execute(sql)
	results = c.fetchall()
	for result in results:
		company_ids.append(result[0])
	
	# get driver speeds
	for date in dates:
		sql = f'SELECT percent_speeding FROM {tbl} WHERE driver_id = ? AND start_date = ?'
		values = (driver_id, date)
		c.execute(sql, values)
		result = c.fetchone()
		
		# use avg speed if there is no
		# data for the week
		if result == None:
			driver_historic_speeds.append(driver_avg)
		# append the driver speed
		else:
			driver_historic_speeds.append(result[0])
	
	# get rtm avg per week
	for date in dates:
		temp_list = []
		
		for driver_id in rtm_ids:
			sql = f'SELECT percent_speeding FROM {tbl} WHERE start_date = ? AND driver_id = ?'
			value = (date, driver_id)
			c.execute(sql, value)
			result = c.fetchone()
			
			try:
				temp_list.append(result[0])
			except:
				pass
		rtm_historic_avg_speeds.append(statistics.mean(temp_list))
		
		if date == dates[-1]:
			rtm_current_speeds.extend(temp_list)

	# get company avg per week
	for date in dates:
		temp_list = []
		
		for driver_id in company_ids:
			sql = f'SELECT percent_speeding FROM {tbl} WHERE start_date = ? AND driver_id = ?'
			value = (date, driver_id)
			c.execute(sql, value)
			result = c.fetchone()
			
			try:
				temp_list.append(result[0])
			except:
				pass
		company_historic_avg_speeds.append(statistics.mean(temp_list))

		if date == dates[-1]:
			company_current_speeds.extend(temp_list)
		
		
	line_chart = generate_line_chart(dates, driver_historic_speeds, rtm_historic_avg_speeds, company_historic_avg_speeds)
	
	processing_data = {
		'plt': line_chart,
		'current_date': dates[-1],
		'driver_name': f'{driver_name}',
		'plt_type': 'avgLineChart',
		'driver_id': target_driver
	}
	
	processed_line_chart = save_plt(processing_data)
	
	plt_paths['lineChart'] = processed_line_chart
	
	line_chart.show()
	line_chart.close()
	
	rtm_histogram = gen_histogram(rtm_current_speeds, driver_historic_speeds[-1])
	
	processing_data = {
		'plt': rtm_histogram,
		'current_date': dates[-1],
		'driver_name': f'{driver_name}',
		'plt_type': 'rtm_histogram',
		'driver_id': target_driver
	}
	
	processed_line_chart = save_plt(processing_data)
	
	plt_paths['rtmHistogram'] = processed_line_chart
	
	rtm_histogram.show()
	rtm_histogram.close()
	
	company_histogram = gen_histogram(company_current_speeds, driver_historic_speeds[-1])
	
	processing_data = {
		'plt': company_histogram,
		'current_date': dates[-1],
		'driver_name': f'{driver_name}',
		'plt_type': 'company_histogram',
		'driver_id': target_driver
	}
	
	processed_line_chart = save_plt(processing_data)
	
	plt_paths['companyHistogram'] = processed_line_chart
	
	company_histogram.show()
	company_histogram.close()
	
	conn.close()
	return plt_paths
	
	

		
	







def generate_report(data_package):
	stats = data_package['stats']
	graph_paths = data_package['graph_paths']
	
	for i in stats:
		print(i)
	
	print(stats['driver_id'])
	











def main(enter_driver=False, driver_num=30150643, print_out=False):
	print('Initializing individual driver report process...\n')

	conn = db_connection()
	c = conn.cursor()
	
	if enter_driver is True:
		driver_num_valid = False
		
		while driver_num_valid is False:
			driver_num = input('Enter driver  number:\n')
			
			# check if num is in db
			driver_num_valid = validate_driver_num(driver_num)
	
	driver_rtm = None
	
	# gather driver data
	data_set = build_data_set(driver_num)
	
	conn.close()
	
	# build analytic dictionary
	analysis_package = analyze_data(data_set, driver_num)
	
	stats = analysis_package['stats']
	data_sets = analysis_package['data_sets']
	
	# graphs will be a dictionary with
	# paths to the graphs
	graphs = build_graphs(driver_num, stats['avg'])
	
	data_package = {
		'graph_paths': graphs,
		'stats': analysis_package['stats']
	}

	
	return data_package
	






if __name__ == '__main__':
	main(print_out=True)
	
	
	
relevent_col_names = {
	'driver_name': 'Driver Name',
	'driver_id': 'Driver Id',
	'rtm': 'RTM',
	'percent_speeding': 'Percent Speeding',
	'max_speed_non_interstate_freeway': 'Max Speed - Non-Interstate',
	'percent_speeding_non_interstate_freeway': 'Percent Speeding  - Non-Interstate',
	'max_speed_interstate_freeway': 'Max Speed - Interstate',
	'percent_speeding_interstate_freeway': 'Percent Speeding - Interstate',
	'worst_incident_date': 'Worst Incident Date',
	'location': 'Worst Incident Location',
	'speed_limit': 'Worst Incident Speed Limit',
	'speed': 'Worst Incident Speed',
	'distance_driven': 'Worst Incident Distance Driven',
	'start_date': 'Worst Incident Start Date',
	'end_date': 'Worst Incident End Date',
	}
