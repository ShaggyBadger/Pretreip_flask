import sys
import os
# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import settings
import requests
import re
import math
import statistics
from src import db_utils
from PIL import Image
import PIL.Image as Image
from io import BytesIO
import matplotlib.pyplot as plt

def construct_img_name(driver_id, date, all_locations=False):
	conn = settings.db_connection()
	c = conn.cursor()
	sql = f'SELECT formated_start_date FROM {settings.speedGaugeData} WHERE start_date = ?'
	value = (date,)
	c.execute(sql, value)
	formatted_date = c.fetchone()[0]
	conn.close()
	
	dir_name = 'maps'
	subdir_name = str(formatted_date)
	chart_dir = settings.MAP_PATH / dir_name / subdir_name
	chart_dir.mkdir(parents=True, exist_ok=True)
	
	if all_locations is Fale:
		img_name = f'{driver_id}_map.png'
		img_path = chart_dir / img_name
	else:
		img_name = f'{driver_id}_full_map.png'
	
	return img_path

def save_map(img, center_coords, zoom):
	# build directory for images
	dir_name = 'maps'
	chart_dir = settings.MAP_PATH / dir_name
	chart_dir.mkdir(parents=True, exist_ok=True)
	
	img_name = f'baseMap_{center_coords}_{zoom}.png'
	img_path = chart_dir / img_name
	
	img.save(img_path)

	return img_path

def build_base_map(center_coords, zoom):
	lat = center_coords[0]
	lon = center_coords[1]

	url = f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&z={zoom}&size=600,400&l=map&pt={lon},{lat},pm2blm&lang=en_US"
	
	response = requests.get(url)

	img = Image.open(BytesIO(response.content))
	img.show()
	
	return img

def haversine(lat1, lon1, lat2, lon2):
	"""
	Calculates the great-circle distance between two points on the Earth 
	using the Haversine formula.
	
	Args:
		lat1, lon1: Latitude and longitude of the first point in decimal degrees.
		lat2, lon2: Latitude and longitude of the second point in decimal degrees.
		
	Returns:
		Distance between the two points in kilometers.
		"""
	R = 6371  # Radius of Earth in kilometers
	
	# Convert latitude and longitude from degrees to radians
	lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
	
	# Haversine formula
	dlat = lat2 - lat1
	dlon = lon2 - lon1
	a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
	
	distance_km = R * c
	distance_miles = distance_km * 0.621371
	
	return distance_miles

def extract_coordinates(url):
	pattern = r"la=([-.\d]+)&lo=([-.\d]+)"
	match = re.search(pattern, url)
	if match:
		lat = float(match.group(1))
		lon = float(match.group(2))
		return lat, lon
	
	else:
		return None

def build_coord_list(target_ids, date_range='latest'):
	"""
	Builds a list of coordinates by querying the database for URLs containing location data.
	
	Args:
		-target_ids (list): A list of driver IDs to filter the query.
		
		-date_range (str, optional): Specifies which dates to include in the query.
			- 'latest' (default): Only includes the most recent date.
			- 'full': Includes all available dates.
	
	Returns:
		list: A list of extracted coordinates (latitude, longitude) from the queried URLs.
	
	Notes:
		- The function retrieves all available dates from the database.
		- It dynamically constructs an SQL query using placeholders for driver IDs and dates.
		- The query fetches URLs from the `settings.speedGaugeData` table based on the given filters.
		- Coordinates are extracted from valid URLs using `extract_coordinates()`.
		- The final list excludes any `None` values.
	"""
	center_lat = 36.0750039
	center_lon = -79.9345196
	
	conn = settings.db_connection()
	c = conn.cursor()

	dates = db_utils.get_all_dates()
	raw_coord_list = []
	
	if date_range == 'latest':
		date_list = [
			dates[-1]
			]
	elif date_range == 'full':
		date_list = [
			date for date
			in dates
			]
			
	# build ?'s for sql'
	driver_id_insertion = ','.join('?' * len(target_ids))
	date_insertion = ','.join('?' * len(date_list))
	
	# build sql query
	sql = f'''
		SELECT url
		FROM {settings.speedGaugeData}
		WHERE driver_id IN ({driver_id_insertion})
		AND start_date IN ({date_insertion})
	'''
	values = (tuple(target_ids) + tuple(date_list))
	
	c.execute(sql, values)
	results = c.fetchall()
	for result in results:
		if result[0] != None:
			raw_coord_list.append(extract_coordinates(result[0]))
			
	cleaned_coord_list = [
		coord for coord
		in raw_coord_list
		if coord != None
		]
		
	return cleaned_coord_list

def latlon_to_pixels(lat, lon, min_lat, max_lat, min_lon, max_lon, img_width, img_height):
	x = (lon - min_lon) / (max_lon - min_lon) * img_width
	y = (1 - (lat - min_lat) / (max_lat - min_lat)) * img_height  # Invert Y-axis
	
	return int(x), int(y)

def temp(coord_list, baseMap_path):
	center_coords = 36.0750039, -79.9345196
	lat_center = center_coords[0]
	lon_center = center_coords[1]
	
	zoom = 8
	
	lat_range = 45 / (2**zoom)
	lon_range = 90 / (2**zoom)
	
	max_lat = lat_center + lat_range
	min_lat = lat_center - lat_range
	max_lon = lon_center + lon_range
	min_lon = lon_center - lon_range
	
	filtered_coords = [
		(lat, lon) for lat, lon
		in coord_list
		if min_lat <= lat <= max_lat
		and min_lon <= lon <= max_lon
		]
	
	img_width = 600
	img_height = 400
	
	pixel_coords = [
		latlon_to_pixels(lat, lon, min_lat, max_lat, min_lon, max_lon, img_width, img_height)
		for lat, lon in filtered_coords
		]
	# Load map image
	map_img = Image.open(baseMap_path)  # Replace with the path to your Yandex map image
	
	# Create figure and plot
	fig, ax = plt.subplots(figsize=(6, 4))
	ax.imshow(map_img)  # Display the map
	
	# Plot scatter points
	x_vals, y_vals = zip(*pixel_coords)  # Extract X, Y positions
	ax.scatter(x_vals, y_vals, color='red', s=10)  # Scatter plot with red dots
	
	# Hide axes
	ax.set_xticks([])
	ax.set_yticks([])
	
	plt.show()

def save_img_blob(driver_id, date, img, column='speed_map'):
	conn = settings.db_connection()
	c = conn.cursor()
	
	img_byte_arr = BytesIO()
	img.save(img_byte_arr, format='PNG')
	img_blob = img_byte_arr.getvalue()
	
	sql = f'UPDATE {settings.speedGaugeData} SET {column} = ? WHERE driver_id = ? AND start_date = ?'
	values = (img_blob, driver_id, date)
	
	c.execute(sql, values)
	conn.commit()
	conn.close()
	
def get_map(url, date, driver_id):
	zoom = 12
	coords = extract_coordinates(url)
	
	img = build_base_map(coords, zoom)
	
	return img

def get_full_map(coord_list, zoom=8):
	lat_list = [
		coord[0] for coord in coord_list
		]
	lon_list = [
		coord[1] for coord in coord_list
		]
		
	center_lat = statistics.mean(lat_list)
	center_lon = statistics.mean(lon_list)
	
	url_insertion = ''
	counter = 0
	
	for coord in coord_list:
		lat = coord[0]
		lon = coord[1]
		
		url_piece = f'{lon},{lat},pm2blm~'
		
		if counter < 100:
			url_insertion += url_piece
			counter +=1
	
	# cut last ~ out of insertion
	edited_url_insertion = url_insertion[:-1]
	
	# build url
	full_url = f'https://static-maps.yandex.ru/1.x/?ll={center_lon},{center_lat}&z={zoom}&size=600,400&l=map&pt={edited_url_insertion}&lang=en_US'
	
	response = requests.get(full_url)
	#print(response.status_code)

	img = Image.open(BytesIO(response.content))
	img.show()
	return img

def controller(driver_id, overwrite_img=False):
	conn = settings.db_connection()
	c = conn.cursor()
	
	sql = f'SELECT url, speed_map, start_date, full_speed_map FROM {settings.speedGaugeData} WHERE driver_id = ? ORDER BY start_date'
	value = (driver_id,)
	c.execute(sql, value)
	results = c.fetchall()
	conn.close()
	
	first_filter = [
		result for result
		in results
		if result[0] is not None
		]
	
	second_filter = [
		result for result
		in first_filter
		if result[0] != '-'
		]
	
	for result in second_filter:
		url = result[0]
		speed_map = result[1]
		date = result[2]
		full_speed_map = result[3]
		
		if speed_map is None or overwrite_img is True:
			img = get_map(url, date, driver_id)
			save_img_blob(driver_id, date, img)
		
		if full_speed_map is None or overwrite_img is True:
			# build full map
			coord_list = [
				extract_coordinates(result[0]) for result
				in second_filter
				]
				
			img = get_full_map(coord_list)
			save_img_blob(driver_id, date, img, column='full_speed_map')
		
	
	



def build_full_map():
	center_lat = 36.0750039
	center_lon = -79.9345196
	center_coords = (center_lat, center_lon)
	zoom = 8
	target_ids = db_utils.gather_driver_ids()
	coord_list = build_coord_list(target_ids, date_range='full')
	baseMap = build_base_map(center_coords, zoom)
	baseMap_path = save_map(baseMap, center_coords, zoom)
	img = temp(coord_list, baseMap_path)
	

if __name__ == '__main__':
	controller(30150643)
	
	#url = f"https://static-maps.yandex.ru/1.x/?ll={lon_center},{lat_center}&z={zoom}&size=600,400&l=map&pt={lon_center},{lat_center},pm2blm&lang=en_US"
