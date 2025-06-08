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
import requests
import console
from io import BytesIO
from PIL import Image
from src import db_utils

def filter_speed_list(spd_lst, max_stdev=3):
	'''
	returns a modified list that
	excludes speeds past a certain 
	standard deviation
	'''
	stdev = statistics.stdev(spd_lst)
	avg = statistics.mean(spd_lst)
	
	max_spd = avg + (max_stdev * stdev)
	
	spd = [speed for speed in spd_lst if speed < max_spd]
	
	return spd
	
def get_percent_change(val1, val2):
	if val2 == 0:
		return ((val1 - val2) / (val2 + 1)) * 100
	else:
		return ((val1 - val2) / (val2)) * 100

def build_location_data(center_coords=settings.km2_coords, zoom=8):
	location_list = db_utils.gather_locations(center=center_coords, max_distance=65)
	
	url_insertion = ''
	counter = 0
	
	for i in location_list:
		coords = i[3]
		lat = coords[0]
		lon = coords[1]
		
		url_piece = f'{lon},{lat},pm2blm~'
		
		if counter < 100:
			url_insertion += url_piece
			counter +=1
	
	edited_url_insertion = url_insertion[:-1]
	
	full_url = f'https://static-maps.yandex.ru/1.x/?ll={center_coords[1]},{center_coords[0]}&z={zoom}&size=600,400&l=map&pt={edited_url_insertion}&lang=en_US'
	
	response = requests.get(full_url)
	#print(response.status_code)

	img = Image.open(BytesIO(response.content))
	img.show()
	
	

def build_analysis(rtm='chris'):
	date_list = db_utils.get_all_dates()
	rtm_ids = db_utils.gather_driver_ids(rtm='chris')
	company_ids = db_utils.gather_driver_ids(rtm='company')
	
	# make list of dicts. key is date, value is filtered speed_list
	rtm_data = []
	company_data = []
	rtm_distances = []
	company_distances = []
	
	# build filtered speed list for company and rtm for each date
	for date in date_list:
		rtm_drivers = db_utils.gather_driver_data(rtm_ids, date)
		company_drivers = db_utils.gather_driver_data(company_ids, date)
		
		rtm_spd_lst = filter_speed_list([dict['percent_speeding'] for dict in rtm_drivers])
		rtm_avg = round(statistics.mean(rtm_spd_lst), 2)
		rtm_median = round(statistics.median(rtm_spd_lst), 2)
		

		
		if len(rtm_data) == 0:
			rtm_avg_percent_change = get_percent_change(rtm_avg, 0)
			rtm_avg_abs_change = rtm_avg - 0
		else:
			prev_rtm_avg = rtm_data[-1]['average']
			rtm_avg_percent_change = get_percent_change(rtm_avg, prev_rtm_avg)
			rtm_avg_abs_change = rtm_avg - prev_rtm_avg
		
		company_spd_lst = filter_speed_list([dict['percent_speeding'] for dict in company_drivers])
		company_avg = round(statistics.mean(company_spd_lst), 2)
		company_median = round(statistics.median(company_spd_lst), 2)
		
		if len(company_data) == 0:
			company_avg_percent_change = get_percent_change(rtm_avg, 0)
			company_avg_abs_change = company_avg - 0
		else:
			prev_company_avg = company_data[-1]['average']
			company_avg_percent_change = get_percent_change(company_avg, prev_company_avg)
			company_avg_abs_change = company_avg - prev_company_avg
		
		rtm_distances = [
			dict['distance_driven'] for dict in rtm_drivers
			if isinstance(dict['distance_driven'], (int, float))
			]
		
		company_distances = [
			dict['distance_driven'] for dict in company_drivers
			if isinstance(dict['distance_driven'], (int, float))
			]
		
		if len(rtm_distances) == 0:
			rtm_distances.append(0)
		if len(company_distances) == 0:
			company_distances.append(0)
		
		rtm_data.append(
			{
				'date': date,
				'rtm_name': rtm.capitalize(),
				'spd_lst': rtm_spd_lst,
				'average': rtm_avg,
				'median': rtm_median,
				'avg_percent_change': round(rtm_avg_percent_change,2),
				'avg_abs_change': round(rtm_avg_abs_change, 2),
				'avg_distance_driven': round(statistics.mean(rtm_distances), 2),
				'distance_list': rtm_distances
			}
		)

		company_data.append(
			{
				'date': date,
				'spd_lst': company_spd_lst,
				'average': company_avg,
				'median': company_median,
				'avg_percent_change': round(company_avg_percent_change, 2),
				'avg_abs_change': round(company_avg_abs_change, 2),
				'avg_distance_driven': round(statistics.mean(company_distances), 2),
				'distance_list': company_distances
			}
		)
	
	data_packet = {
		'rtm': rtm_data,
		'company': company_data,
		'rtm_name': db_utils.get_manager(rtm_ids[0])
	}
	
	return data_packet
		
		
	
		


# auto-reload module to prevent cache issues
if 'analysis' in sys.modules:
	importlib.reload(sys.modules['analysis'])

if __name__ == '__main__':
	
	#a = build_analysis()
	orlando_coords = (28.538336, -81.379234)
	atlanta_coords = (33.7501, -84.3885)
	roanoke_coords = (37.270969, -79.941429)
	chesapeake_coords = (36.779591, -76.288376)
	build_location_data()
