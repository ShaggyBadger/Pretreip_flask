import settings
from src import db_utils
from collections import deque
import console

def print_driver_info(driver_info):
	print(f'{driver_info[0][0]}: {driver_info[0][1]}')
	
	for row in driver_info:
		print(f'{row[4]}: {row[2]} / {row[3]}')

def get_dates_until(max_date):
	conn = settings.db_connection()
	c = conn.cursor()
	
	sql = f'SELECT DISTINCT start_date FROM {settings.speedGaugeData} WHERE start_date <= ? ORDER BY start_date ASC'
	value = (max_date,)
	c.execute(sql, value)
	results = c.fetchall()
	
	date_list = [
		result[0] for result in results
		]
	
	conn.close()
	return date_list

def delete_driver(driver_info, conn):
	driver_id = driver_info[0][1]
	console.clear()
	c = conn.cursor()
	
	selection_valid = False
	while selection_valid is False:
		valid_options = ['1', '2', '3']
		console.clear()
		print(driver_id)
		print_driver_info(driver_info)
		print('\nChoose what option you want:')
		selection = input('1 - delete all records\n2 - delete only generated records\n3 - dont delete anything and keep going\n\nEnter selection: ')
		
		if str(selection) in valid_options:
			selection_valid = True
	
	if selection == '1':
		sql = f'DELETE FROM {settings.speedGaugeData} WHERE driver_id = ?'
		sql2 = f'DELETE FROM {settings.driverInfo} WHERE driver_id = ?'
		value = (driver_id,)
		c.execute(sql, value)
		c.execute(sql2, value)
		
		input('Driver deleted from the database. Good riddance.\n\nPress enter to continue...')
	
	elif selection == '2':
		sql = f'DELETE FROM {settings.speedGaugeData} WHERE driver_id = ? AND percent_speeding_source = ?'
		values = (driver_id, 'generated')
		c.execute(sql, values)

		
		input('Records deleted from the database. Good riddance.\n\nPress enter to continue...')
	
	elif selection == '3':
		input('Ok, not doing anything with these redords.\n\npress enter to continue....')
	
	conn.commit()
	c.close()

def controller():
	conn = settings.db_connection()
	c = conn.cursor()
	
	full_date_list = db_utils.get_all_dates()
	cur_date = full_date_list[-1]
	
	gen_status = {}
	
	for date in full_date_list:
		sql = f'SELECT driver_id FROM {settings.speedGaugeData} WHERE percent_speeding_source = ? AND start_date = ?'
		values = ('generated', date)
		c.execute(sql, values)
		results = c.fetchall()
		
		gen_list = [
			result[0] for result in results
			]
		
		gen_status[date] = gen_list
	
	driver_tracker = {}
	inactive_drivers = set()
	sliding_window = deque(maxlen=4)
	
	for date in full_date_list:
		driver_list = set(gen_status[date])
		sliding_window.append(driver_list)
		
		if len(sliding_window) < 4:
			continue
		
		appearance_count = {}
		for week in sliding_window:
			for driver in week:
				appearance_count[driver] = appearance_count.get(driver, 0) + 1
		for driver, count in appearance_count.items():
			if count == 4:
				inactive_drivers.add(driver)

	for driver_id in inactive_drivers:
		deletion_dict = {}
		sql = f'SELECT driver_name, driver_id, percent_speeding, percent_speeding_source, human_readable_start_date FROM {settings.speedGaugeData} WHERE driver_id = ? ORDER BY start_date ASC'
		value = (driver_id,)
		c.execute(sql, value)
		results = c.fetchall()
		
		print_driver_info(results)
		
		selection = input('\nEnter y to delete this driver')
			
		if selection == 'y':
			delete_driver(results, conn)
		
		console.clear()
	
	conn.close()
	
if __name__ == '__main__':
	temp()
