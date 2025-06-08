import settings
import os
import importlib
import db_management
from src import analysis
from src import visualizations
from src import db_utils
from src import processing
from src import reports
from src import individualDriver
from idr_src import idr_analysis
from idr_src import idr_visualizations
from idr_src import idr_reports
from idr_src import idr_map
import matplotlib.pyplot as plt
import console
import json

def inspection():
	import inspect
	functions = inspect.getmembers(db_utils, inspect.isfunction)
	
	for name, func in functions:
		docstring = inspect.getdoc(func) or 'no docstring provided'
		print(f'{name}\n')
		print(docstring)
		print('\n******\n')

def idr(enter_driver=True, driver_id=30150643, stats_package=None):
	'''
	this can work from main seledtion
	screen, in which case enter driver 
	is True
	
	also can use this to run report on
	driver via the weekly analysis. 
	maybe send through the outliers
	and get indivual reports on them
	
	in that case enter_driver is set 
	to False and the driver_id needs
	to be overriden as well with the
	target id
	'''
	# get driver_id from user
	ids = {
		1201619: 'rodrick',
		30199025: 'perkins',
		30072074: 'jesse',
		5055241: 'brent',
		30188814: 'jamie',
		1110492: 'danny',
		30069398: 'ron',
		1152694: 'charles',
		30202984: 'john r',
		30190385: 'travis',
		30150643: 'me',
		30097394: 'Jayson Ruiz'
	}
	
	if enter_driver is True:
		valid_input = False
		
		while valid_input is False:
			console.clear()
			for i in ids:
				print(f'{i}: {ids[i]}')
			print('********\n')

			selection = input('Enter Driver Number: ')
			
			if db_utils.verify_driver_id(selection) is True:
				valid_input = True
				driver_id = int(selection)
			else:
				console.clear()
				input(f'{selection} is not a valid input in the database. please enter another number...')
	
	# build company and rtm stats
	if stats_package == None:
		stats_package = analysis.build_analysis()
	
	
	# collect all driver dictionaries
	driver_dicts = db_utils.idr_driver_data(driver_id)
	
	# build driver stats dict
	driver_stats = idr_analysis.idr_analytics(driver_dicts, driver_id, stats_package)
	
	# complete stats package
	stats_package['driver'] = driver_stats
	
	# build visualizations
	#plt_paths = visualizations.retrieve_plts(driver_stats['date_list'][-1])
	idr_visuals = idr_visualizations.controller(stats_package, driver_id)
	
	plt_paths = {
		'driver_graph': idr_visuals['avg_line_chart'],
		'distance_driven_graph': idr_visuals['distance_driven_chart']
	}
	
	# build map blobs in db
	idr_map.controller(driver_id)
	
	# build report
	report_path = idr_reports.create_report(stats_package, plt_paths)

def weekly_analysis():
	stat_packet = analysis.build_analysis()
	
	rtm_analysis = stat_packet['rtm']
	company_analysis = stat_packet['company']
	rtm_name = stat_packet['rtm_name']

	plt_paths = visualizations.controller(stat_packet)
	
	stats_json = json.dumps(stat_packet)
	plt_paths_json = json.dumps(plt_paths, default=str)
	
	# save json data in the db
	db_utils.store_json_data(stats_json, plt_paths_json, rtm_name, db_utils.get_max_date())		
	
	report_path = reports.create_report(stat_packet, plt_paths)

def run_program():
	selection_dict = {
		'1': 'process spreadsheets',
		'2': 'run weekly analytics',
		'3': 'Run individual driver report',
		'4': 'Purge generated speeds from db'
	}
	
	print('please make selection:')
	for i in selection_dict:
		print(f'\n{i}: {selection_dict[i]}')
	selection = input()
	
	console.clear()
	if str(selection) == str(1):
		processing.main()
	
	elif str(selection) == str(2):
		weekly_analysis()
	
	elif str(selection) == str(3):
		ids = {
			1201619: 'rodrick',
			30199025: 'perkins',
			30072074: 'jesse',
			5055241: 'brent',
			30188814: 'jamie',
			1110492: 'danny',
			30069398: 'ron',
			1152694: 'charles',
			30202984: 'john r',
			30190385: 'travis',
			5019067: 'Pete',
			5000688: 'billy',
			30219248: 'mike_Russ',
			30115589: 'john clayton',
			30186215: 'ibraham',
			30150643: 'me',
			30135448: 'carmello',
			30186711: 'ingram',
			30055670: 'david heath',
			30110871: 'Donald Howell',
			30227642: 'Oscar',
			5053272: 'David Thompson',
			32010202: 'amber shepp',
			30097394: 'Jayson Ruiz'
		}
		
		stats = analysis.build_analysis()
		for i in ids:
			print('\n\n')
			print(ids[i])
			idr(
				enter_driver=False,
				driver_id=i,
				stats_package=stats
				)
	
	elif str(selection) == str(4):
		db_management.controller()

if __name__ == '__main__':
	importlib.reload(visualizations)
	importlib.reload(reports)
	importlib.reload(db_utils)
	importlib.reload(idr_analysis)
	importlib.reload(idr_reports)
	importlib.reload(idr_visualizations)
	importlib.reload(idr_map)
	run_program()
	#run_weekly_analyis()
	#weekly_analysis()
