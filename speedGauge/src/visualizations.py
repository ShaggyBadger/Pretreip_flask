import sys, os
import platform
import statistics
# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Now you can import settings
import settings
import matplotlib.pyplot as plt
from matplotlib import style
style.use('seaborn-darkgrid')
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path
from src import db_utils

# check if system is pythonista. if not then use tkinter for visualizations
system = platform.system()
is_pythonista = sys.platform == 'ios'

if system != 'Darwin' and is_pythonista:
	plt.switch_backebd('TkAgg')

'''*****Begin The Functions!****'''
def retrieve_plts(date):
	conn = settings.db_connection()
	c = conn.cursor()
	
	sql = f'SELECT start_date, rtm, plt_type, plt_name, plt_path FROM {settings.imgStorage} WHERE start_date = ?'
	value = (date,)
	c.execute(sql, value)
	results = c.fetchall()
	for i in results:
		print(i)
		print('')
	
	conn.close()

def save_plt(plt, date, plt_type, rtm='chris'):
	scope = f'RTM_{rtm}'
	conn = settings.db_connection()
	c = conn.cursor()
	sql = f'SELECT DISTINCT formated_start_date FROM {settings.speedGaugeData} WHERE start_date = ?'
	value = (date,)
	c.execute(sql, value)
	formated_date = c.fetchone()[0]
	
	# build directory for images
	dir_name = 'charts_' + str(formated_date)
	chart_dir = settings.WEEKLY_REPORTS_PATH / dir_name
	chart_dir.mkdir(parents=True, exist_ok=True)
	
	img_name = f'{rtm.capitalize()}_{plt_type}_{str(formated_date)}.png'
	img_path = chart_dir / img_name
	
	plt.savefig(img_path, dpi=300, bbox_inches='tight')
	
	# build the blob
	with open(img_path, "rb") as file:
		blob_data = file.read()
	
	# update the db
	sql = f'SELECT id FROM {settings.imgStorage} WHERE start_date = ? AND plt_name = ?'
	values = (date, img_name)
	c.execute(sql, values)
	existing_record = c.fetchone()
	
	if existing_record is not None:
		sql = f'UPDATE {settings.imgStorage} SET start_date = ?, rtm = ?, plt_type = ?, plt_name = ?, plt_path = ?, plt_blob = ? WHERE id = ?'
		values = (date, rtm, plt_type, img_name, str(img_path), blob_data, existing_record[0])
		c.execute(sql, values)
	else:
		sql = f'INSERT INTO {settings.imgStorage} (start_date, rtm, plt_type, plt_name, plt_path, plt_blob) VALUES (?, ?, ?, ?, ?, ?)'
		values = (date, rtm, plt_type, img_name, str(img_path), blob_data)
		c.execute(sql, values)
	
	conn.commit()
	conn.close()
	return img_path


def build_histogram(stats, scope, numBins=15, log_setting=False):
	'''
	build a histogram with raw speed list settled behind the filtered
	speed list. 
	
	set name of histogram to either Company or to RTM - rtm_name. Default rtm is chris.
	'''
	# get dates list
	date_list = db_utils.get_all_dates()
	cur_week = date_list[-1]
	
	if scope == 'company':
		dict_list = stats['company']
		title_scope = 'Company-Wide'
	else:
		dict_list = stats['rtm']
		title_scope = f'RTM - {scope.capitalize()}'
	
	# collect speed lists
	target_dict = next((d for d in dict_list if d['date'] == cur_week), None)
	
	x_label = 'Speeding Percentage'
	y_label = 'Number Of Drivers'
	title = f'{title_scope}: Weekly Distribution Of Speeding Percentages'
	
	plt.figure()
	plt.hist(
		target_dict['spd_lst'],
		bins=numBins,
		edgecolor='black',
		color=settings.swto_blue,
		label=f'{title_scope} percent_speeding list',
		log=log_setting
		)
	
	plt.axvline(target_dict['average'], label=f'{title_scope}: Average ({target_dict["average"]})', color='red')
	
	plt.xlabel(x_label)
	plt.ylabel(y_label)
	plt.title(title)
	plt.legend()
	
	plt_type = f'Histogram_{scope.capitalize()}'
	plt_path = save_plt(plt, cur_week, plt_type)
	
	plt.show()
	plt.close()
	plt.clf()
	
	return plt_path
	
def build_scatter(stats):
	rtm_stats = stats['rtm']
	date_list = db_utils.get_all_dates()
	
	x = []
	y = []
	
	for date in date_list:
		for dict in rtm_stats:
			if dict['date'] == date:
				for spd in dict['spd_lst']:
					x.append(date)
					y.append(spd)
	
	plt.figure()
	plt.scatter(
		x,
		y
		)
	plt.show()
	plt.close()
	
	return plt

def build_line_chart(stats, stat_selection, rtm='chris'):
	if stat_selection == 'average':
		stat_function = statistics.mean
	else:
		stat_function = statistics.median
	
	rtm_stats = stats['rtm']
	company_stats = stats['company']
	
	dates = db_utils.get_all_dates()
	dates2 = [datetime.strptime(date, '%Y-%m-%d %H:%M') for date in dates]
	
	x_label = 'Date'
	y_label = f'{stat_selection.capitalize()} Percent Speeding'
	title = f'Historical Distribution of {stat_selection.capitalize()} Percent Speeding'
	rtm_label = f'Rtm {stat_selection.capitalize()}'
	company_label = f'Company {stat_selection.capitalize()}'
	
	company_line_data = []
	rtm_line_data = []
	
	for date in dates:	
		target_dict = None
		for dict in rtm_stats:
			if dict['date'] == date:
				rtm_line_data.append(dict[stat_selection])
		
		for dict in company_stats:
			if dict['date'] == date:
				company_line_data.append(dict[stat_selection])
		
	plt.figure(constrained_layout=True)
	#plt.figure(figsize=(6,2))
	plt.tight_layout()

	plt.plot(dates2, rtm_line_data, label=rtm_label, color=settings.swto_blue, linestyle='-', linewidth=3)
	
	plt.plot(dates2, company_line_data, label=company_label, color='green', linestyle='-', linewidth=3)
	
	if stat_selection == 'average':
		plt.axhline(y=0.4, color='red', linewidth=1, label='percent_speeding Objective: 0.4%')
	
	# Set major locator to one tick per month
	plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
	
	# Format the date labels to show the month and year (e.g., Jan 2024)
	plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
	
	
	# Rotate the labels for readability
	plt.xticks(rotation=45)
	
	ax = plt.gca()
	ax.yaxis.set_label_position("right")
	ax.yaxis.tick_right()
	#ax.set_title(title, fontsize=8)
	#ax.legend(["Line 1"], fontsize=8, loc="upper left", bbox_to_anchor=(1, 1))
	
	# Automatically adjust layout to avoid clipping
	#plt.tight_layout()
	#plt.subplots_adjust(bottom=0.15, left=0.15)  # Adjust bottom and left margins
	
	plt.xlabel(x_label)
	plt.ylabel(y_label)
	plt.title(title)
	plt.legend()
	#plt.figure(figsize=(6,4))
	#plt.tight_layout()
	
	plt_type = f'LineChart_{stat_selection.capitalize()}'
	plt_path = save_plt(plt, dates[-1], plt_type)
	
	plt.show()
	plt.close()
	plt.clf()
	
	return plt_path

def build_distance_line_chart(stats, stat_selection, rtm='chris'):
	if stat_selection == 'average':
		stat_function = statistics.mean
	else:
		stat_function = statistics.median
	
	rtm_stats = stats['rtm']
	company_stats = stats['company']
	
	dates = db_utils.get_all_dates()
	dates2 = [datetime.strptime(date, '%Y-%m-%d %H:%M') for date in dates]
	
	x_label = 'Date'
	y_label = f'{stat_selection.capitalize()} Distance Driven'
	title = f'Historical Distribution of {stat_selection.capitalize()} Distance Driven'
	rtm_label = f'Rtm {stat_selection.capitalize()}'
	company_label = f'Company {stat_selection.capitalize()}'
	
	company_line_data = []
	rtm_line_data = []
	
	for date in dates:	
		target_dict = None
		for dict in rtm_stats:
			if dict['date'] == date:
				distance_list = dict['distance_list']
				rtm_line_data.append(round(stat_function(distance_list),2))
		
		for dict in company_stats:
			if dict['date'] == date:
				distance_list = dict['distance_list']
				company_line_data.append(round(stat_function(distance_list),2))
		
	plt.figure(constrained_layout=True)
	#plt.figure(figsize=(6,2))
	plt.tight_layout()

	plt.plot(dates2, rtm_line_data, label=rtm_label, color=settings.swto_blue, linestyle='-', linewidth=3)
	
	plt.plot(dates2, company_line_data, label=company_label, color='green', linestyle='-', linewidth=3)
	
	if stat_selection == 'average':
		plt.axhline(y=0.4, color='red', linewidth=1, label='percent_speeding Objective: 0.4%')
	
	# Set major locator to one tick per month
	plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
	
	# Format the date labels to show the month and year (e.g., Jan 2024)
	plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
	
	
	# Rotate the labels for readability
	plt.xticks(rotation=45)
	
	ax = plt.gca()
	ax.yaxis.set_label_position("right")
	ax.yaxis.tick_right()
	#ax.set_title(title, fontsize=8)
	#ax.legend(["Line 1"], fontsize=8, loc="upper left", bbox_to_anchor=(1, 1))
	
	# Automatically adjust layout to avoid clipping
	#plt.tight_layout()
	#plt.subplots_adjust(bottom=0.15, left=0.15)  # Adjust bottom and left margins
	
	plt.xlabel(x_label)
	plt.ylabel(y_label)
	plt.title(title)
	plt.legend()
	#plt.figure(figsize=(6,4))
	#plt.tight_layout()
	
	plt_type = f'distance_LineChart_{stat_selection.capitalize()}'
	plt_path = save_plt(plt, dates[-1], plt_type)
	
	plt.show()
	plt.close()
	plt.clf()
	
	return plt_path
	
def build_percent_change_line_chart(stats, rtm='chris'):
	
	rtm_stats = stats['rtm']
	company_stats = stats['company']
	#style.use('dark_background')
	
	dates = db_utils.get_all_dates()
	dates2 = [datetime.strptime(date, '%Y-%m-%d %H:%M') for date in dates]
	
	x_label = 'Date'
	y_label = f'Change in Percent Speeding'
	title = f'Historical Distribution Of Percent Change In Percent Speeding'
	rtm_label = f'Rtm Percent Change'
	company_label = f'Company Percent Change'
	
	company_line_data = []
	rtm_line_data = []
	
	for date in dates:	
		target_dict = None
		for dict in rtm_stats:
			if dict['date'] == date:
				rtm_line_data.append(dict['avg_percent_change'])
		
		for dict in company_stats:
			if dict['date'] == date:
				company_line_data.append(dict['avg_percent_change'])
		
	plt.figure(constrained_layout=True)
	plt.plot(dates2, rtm_line_data, label=rtm_label, color=settings.swto_blue, linestyle='-', linewidth=3)
	
	plt.plot(dates2, company_line_data, label=company_label, color='green', linestyle='-', linewidth=3)
	
	# Set major locator to one tick per month
	plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
	
	# Format the date labels to show the month and year (e.g., Jan 2024)
	plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
	
	# Rotate the labels for readability
	plt.xticks(rotation=45)
	
	ax = plt.gca()
	ax.yaxis.set_label_position("right")
	ax.yaxis.tick_right()
	
	plt.axhline(y=0, color='red', linewidth=1, label='The 0 Line')
	
	# Automatically adjust layout to avoid clipping
	#plt.tight_layout()
	#plt.subplots_adjust(bottom=0.15, left=0.15)  # Adjust bottom and left margins
	
	plt.xlabel(x_label)
	plt.ylabel(y_label)
	plt.title(title)
	plt.legend()
	
	plt_type = f'LineChart_percent_change'
	plt_path = save_plt(plt, dates[-1], plt_type)
	
	plt.show()
	plt.close()
	plt.clf()
	
	return plt_path
	
def controller(stats, rtm='chris'):
	rtm_stats = stats['rtm']
	company_stats = stats['company']
	
	'''build histograms'''
	# build rtm histogram
	rtm_histo_path = build_histogram(stats, rtm, log_setting=False)
	company_histo_path = build_histogram(stats, 'company', log_setting=False)
	
	'''build scatter plt'''
	#rtm_scatter = build_scatter(rtm_stats)
	
	'''build line charts'''
	avg_plt_path = build_line_chart(stats, 'average', rtm='chris')
	median_plt_path = build_line_chart(stats, 'median', rtm='chris')
	
	'''build distance line chart'''
	avg_distance_chart_path = build_distance_line_chart(stats, 'average')
	median_distance_chart_path = build_distance_line_chart(stats, 'median')
	
	plt_paths = {
		'rtm_histo_path': rtm_histo_path,
		'company_histo_path': company_histo_path,
		'avg_plt_path': avg_plt_path,
		'median_plt_path': median_plt_path,
		'avg_distance_plt_path': avg_distance_chart_path,
		'median_distance_plt_path': median_distance_chart_path
	}
	
	return plt_paths
	
def all_chart_styles(stats):
		for s in style.available:
			style.use(s)
			print(s)
			build_line_chart(stats, 'average', rtm='chris')
			#build_histogram(stats, 'company')
			#build_histogram(stats, 'chris')
			#build_scatter(stats)
			print('****************\n')
	
if __name__ == '__main__':
	from src import analysis
	stats = analysis.build_analysis()

	#print(style.available)
	#style.use('seaborn-poster')
	#build_histogram(stats, 'chris')
	#build_histogram(stats, 'company')
	#build_scatter(stats)
	#build_line_chart(stats, 'average', rtm='chris')
	controller(stats)
	#build_percent_change_line_chart(stats)
	#all_chart_styles(stats)

	pass

	


