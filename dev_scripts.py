import json
import sqlite3
from flask_app import models, settings
import speedGauge_app

from rich.traceback import install
from rich import print
install()

class Initialize:
  '''
  Class used to initialize the project
  '''
  def __init__(self, automatic_mode=False):
    # Define the base directory for speedGauge files
    self.speedgauge_base_dir = settings.SPEEDGAUGE_DIR
    self.processed_dir = settings.PROCESSED_SPEEDGAUGE_PATH
    self.unprocessed_dir = settings.UNPROCESSED_SPEEDGAUGE_PATH

    if automatic_mode is True:
      # if this is set to true, then go ahead and just automatically run this thing.
      self.standard_flow()
  def standard_flow(self):
    '''General controller method that will automatically flow through and set everything up'''
    self.construct_dirs()
    self.initialize_db()
    self.processess_speedgauge()
  def initialize_db(self):
    '''automated database creation. This will populate the users table with all the id's from my
    company. Later on anyone can register to use the program as well.'''
    print('Initializing the database...')
    models_util = models.Utils(debug_mode=False)
    models_cli_util = models.CLI_Utils(debug_mode=False)
    sgProcessor = speedGauge_app.sgProcessor.Processor()

    # build the database
    print('Building the Database....')
    models_util.build_db()

    # Enter users from the json file
    print('\nEntering users from json file....')
    models_cli_util.enter_users_from_json()

    # build the speedGauge table in the database
    print('\nCreating speedGauge table....')
    self.create_table_from_json()

    # Populate the speedGauge table with all the files we have
    print('Populating the speedGauge table...')
    sgProcessor.standard_flow()
  def construct_dirs(self):
    '''Method to build necessary directories'''
    dirs_to_construct = [
      self.unprocessed_dir,
      self.processed_dir
    ]

    for directory in dirs_to_construct:
      try:
        # parents=True creates parent directories if they don't exist
        # exist_ok=True prevents an error if the directory already exists
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Directory ensured: {directory}")
      except OSError as e:
        print(f"Error creating directory {directory}: {e}")
  def processess_speedgauge(self):
    '''stick all speedguage files into the database for initial setup'''
    processor = speedGauge_app.sgProcessor.Processor()
    processor.standard_flow()
  def create_table_from_json(self, json_file=None, table_name='speedGauge', debug=False):
    '''create table to hold speedGauge data'''
		# default to the pre_made json file if none is provided
    if json_file is None:
      json_file = settings.SPEEDGAUGE_DIR / 'speedGauge_table.json'
			
		# Load JSON data from file
    with open(json_file, 'r', encoding='utf-8') as file:
      column_info = json.load(file)
			
    # Construct SQL CREATE TABLE statement
    columns_sql = ",\n    ".join([f'"{column}" {datatype}' for column, datatype in column_info.items()])
    create_table_sql = f'''
    CREATE TABLE IF NOT EXISTS "{table_name}" (
      {columns_sql}
      );
    '''
    
    # Print the SQL for debugging
    if debug is True:
      print("Executing SQL:\n", create_table_sql)
    
    # Connect to the database and execute SQL
    conn = self.db_conn()
    c = conn.cursor()
    c.execute(create_table_sql)
    conn.commit()
    conn.close()
  def db_conn(self):
    '''Just an easy way to get database connection'''
    conn = sqlite3.connect(settings.db_name, timeout=10)
    return conn


if __name__ == '__main__':
  dbManager = speedGauge_app.dbManagement.DbManagement()
  dbManager.gen_interpolated_speeds()
