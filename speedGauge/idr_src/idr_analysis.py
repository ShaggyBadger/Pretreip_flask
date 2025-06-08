import sys, os
from pathlib import Path
import importlib
# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# Now you can import settings
import settings
import numpy as np
import math
import statistics
import sqlite3
import console
import re
from src import db_utils
from src import analysis

def get_percent_change(val1, val2):
	if val2 == 0:
		return ((val1 - val2) / (val2 + 1)) * 100
	else:
		return ((val1 - val2) / (val2)) * 100

def get_lat_long(url):
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

def get_slope(spd_lst):
	'''
	Calculate the slope of a linear regression line for a given list of speed values.
	
	This function performs a simple linear regression using NumPy's `polyfit()` to determine 
	the trend of the provided speed values over time (assumed to be sequential weeks).
	
	Parameters:
		spd_lst (list of float): A list of speed values representing weekly averages.
	
	Returns:
		float: The slope of the regression line. 
		- A positive slope indicates an increasing trend.
		- A negative slope indicates a decreasing trend.
		- A slope close to zero suggests no significant trend.
	'''
	week_lst = np.arange(1, len(spd_lst) + 1)
	slope, intercept = np.polyfit(week_lst, spd_lst, 1)
	
	return slope
	

def idr_analytics(driver_dicts, driver_id, general_stats):
	# get current dict
	cur_dict = driver_dicts[-1]
	#target_dict = driver_dicts[18]
	dates = [
		dict['start_date']
		for dict in driver_dicts
		]
	
	rtm_stats = general_stats['rtm']
	rtm_name = general_stats['rtm_name']
	company_stats = general_stats['company']
	
	#for i in rtm_stats:
		#print(i)
	
	# if driver is new and only has one week of data, just use that dict
	if len(driver_dicts) > 1:
		prev_dict = driver_dicts[-2]
	else:
		prev_dict = driver_dicts[-1]
	
	'''build stats'''
	# get percent_speeding list
	speed_list = [
		dict['percent_speeding'] for dict in driver_dicts
		]
	
	distance_driven_list = [
		dict['distance_driven'] for dict in driver_dicts
		]
	
	# clear out None entries
	adjusted_distance_driven_list = [
		d if d is not None
		else 0 for d
		in distance_driven_list
		]
	
	# get list of incident locations
	incident_locations = [
		dict['location']
		for dict
		in driver_dicts
		if dict['location'] not in ['-', None]
		]
	
	# get lat and long info for incident locations
	incident_coords = []
	
	for dict in driver_dicts:
		coords = get_lat_long(str(dict['url']))
		
		if coords != None:
			incident_coords.append(coords)
			
	avg = statistics.mean(speed_list)
	slope = get_slope(speed_list)
	median = statistics.median(speed_list)
	mode = statistics.mode(speed_list)
	
	stats = {
		'driver_id': driver_id,
		'driver_dicts': driver_dicts,
		'date_list': dates,
		'speed_list': speed_list,
		'avg': round(avg, 2),
		'median': round(median, 2),
		'mode': round(mode, 2),
		'slope': round(slope, 2),
		'distance_driven_list': adjusted_distance_driven_list
	}
	
	return stats



if __name__ == '__main__':
	driver_id = 30219248
	
	driver_dicts = db_utils.idr_driver_data(driver_id)
	
	general_stats = analysis.build_analysis()
	
	a = idr_analytics(driver_dicts, driver_id, general_stats)
	
	pass
	
'''
columns to work with:
	id
	driver_name
	driver_id
	vehicle_type
	percent_speeding
	max_speed_non_interstate_freeway
	percent_speeding_non_interstate_freeway
	max_speed_interstate_freeway
	percent_speeding_interstate_freeway
	worst_incident_date
	incident_location
	speed_limit
	speed
	speed_cap
	custom_speed_restriction
	distance_driven
	url
	location
	percent_speeding_numerator
	percent_speeding_denominator
	incidents_interstate_freeway
	observations_interstate_freeway
	incidents_non_interstate_freeway
	observations_non_interstate_freeway
	difference
	start_date
	end_date
	formated_start_date
	formated_end_date
	human_readable_start_date
	human_readable_end_date
	percent_speeding_source
'''
