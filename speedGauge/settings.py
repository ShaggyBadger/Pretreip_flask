from pathlib import Path


'''
establish paths to various  directories for use in other parts of da program
'''
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

# root directory
BASE_DIR = Path(__file__).parent

# Main directories inside root
IMG_PATH = BASE_DIR / 'images'
REPORTS_PATH = BASE_DIR / 'reports'
IDR_REPORTS_PATH = BASE_DIR / 'idr_reports'

# Nested directories
IMG_ASSETS_PATH = IMG_PATH / 'assets'
MAP_PATH = IMG_PATH / 'maps'
WEEKLY_REPORTS_PATH = IMG_PATH / 'weeklyReports'
DATA_PATH = BASE_DIR / 'data'

# path to unprocessed directory
UNPROCESSED_PATH = DATA_PATH / 'unprocessed'

# path to processed directory
PROCESSED_PATH = DATA_PATH / 'processed'

# path to src directory
SRC_PATH = BASE_DIR / 'src'

# path to database directory
DATABASE_PATH = BASE_DIR / 'database'

# path to actual speedGuage.db
DB_PATH = DATABASE_PATH / 'speedGauge.db'

'''column names and types for db not sure if I should include id'''
# aka driverInfo
driverInfoTbl_column_info = {
	'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
	'driver_name': 'TEXT',
	'driver_id': 'INTEGER',
	'rtm': 'TEXT',
	'terminal': 'TEXT',
	'shift': 'TEXT'
}

# aka speedGaugeData
mainTbl_column_info = {
	'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
	'driver_name': 'TEXT',
	'driver_id': 'INTEGER',
	'vehicle_type': 'TEXT',
	'percent_speeding': 'REAL',
	'max_speed_non_interstate_freeway': 'REAL',
	'percent_speeding_non_interstate_freeway': 'REAL',
	'max_speed_interstate_freeway': 'REAL',
	'percent_speeding_interstate_freeway': 'REAL',
	'worst_incident_date': 'TEXT',
	'incident_location': 'TEXT',
	'speed_limit': 'INTEGER',
	'speed': 'INTEGER',
	'speed_cap': 'TEXT',
	'custom_speed_restriction': 'TEXT',
	'distance_driven': 'INTEGER',
	'url': 'TEXT',
	'location': 'TEXT',
	'percent_speeding_numerator': 'REAL',
	'percent_speeding_denominator': 'REAL',
	'incidents_interstate_freeway': 'REAL',
	'observations_interstate_freeway': 'REAL',
	'incidents_non_interstate_freeway': 'REAL',
	'observations_non_interstate_freeway': 'REAL',
	'difference': 'INTEGER',
	'start_date': 'TEXT',
	'end_date': 'TEXT',
	'formated_start_date': 'TEXT',
	'formated_end_date': 'TEXT',
	'human_readable_start_date': 'TEXT',
	'human_readable_end_date': 'TEXT',
	'percent_speeding_source': 'TEXT',
	'speed_map': 'BLOB',
	'full_speed_map': 'BLOB'
	}

imgStorageTbl_column_info = {
	'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
	'start_date': 'TEXT',
	'rtm': 'TEXT',
	'plt_type': 'TEXT',
	'plt_name': 'TEXT',
	'plt_path': 'TEXT',
	'plt_blob': 'BLOB'
}

analysisStorageTbl_column_info = {
	'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
	'start_date': 'TEXT',
	'rtm': 'TEXT',
	'stats': 'TEXT',
	'plt_paths': 'TEXT'
}

# easy color reference
red = '#ff2400'
green = '#03ac13'
warning_orange = '#ffbc37'
swto_blue = '#0b3e69'

# Unicode arrows: ↑ (2191) and ↓ (2193)
up_arrow = '&#x2191;'
down_arrow = '&#x2193;'

# univeral refrence source. handy.
speedGaugeData = 'speedGaugeData'
driverInfo = 'driverInfo'
imgStorage = 'imgStorage'
analysisStorage = 'analysisStorage'
