import json
import pymysql
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

    # establist connection to the database
    self.models_util = models.Utils(debug_mode=False)
    self.models_cli_util = models.CLI_Utils(debug_mode=False)
    self.sgProcessor = speedGauge_app.sgProcessor.Processor(self.models_util)
    self.db_conn = self.models_util.get_db_connection()

    if automatic_mode is True:
      # if this is set to true, then go ahead and just automatically run this thing.
      self.standard_flow()
  
  def standard_flow(self):
    '''General controller method that will automatically flow through and set everything up'''
    self.construct_dirs()
    self.initialize_db()
  
  def initialize_db(self):
    '''automated database creation. This will populate the users table with all the id's from my
    company. Later on anyone can register to use the program as well.'''
    print('Initializing the database...')
    

    # build the database
    print('Building the Database....')
    self.models_util.build_db()

    # Enter users from the json file
    print('\nEntering users from json file....')
    self.models_cli_util.enter_users_from_json()

    # build the speedGauge table in the database
    print('\nCreating speedGauge table....')
    self.create_table_from_json()

    # Populate the speedGauge table with all the files we have
    print('Populating the speedGauge table...')
    self.sgProcessor.standard_flow()
  
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
    self.sgProcessor.standard_flow()
  
  def create_table_from_json(self, json_file=None, table_name='speedGauge_data_tbl_name', debug=False):
    '''create table to hold speedGauge data'''
    # default to the pre_made json file if none is provided
    if json_file is None:
      json_file = settings.SPEEDGAUGE_DIR / 'speedGauge_table.json' # Make sure this path is correct
      
    # Load JSON data from file
    with open(json_file, 'r', encoding='utf-8') as file:
      column_info = json.load(file)
      
    columns = []
    table_options = ""

    # Separate columns from table_options
    for column, definition in column_info.items():
        if column == "table_options":
            table_options = definition # Store the table options
        else:
            # Construct column definition without double quotes for MySQL compatibility
            columns.append(f"{column} {definition}")
    
    # Join column definitions with proper indentation
    columns_sql = ",\n      ".join(columns)

    # Construct SQL CREATE TABLE statement
    # Remove quotes around table_name for MySQL compatibility
    create_table_sql = f'''
    CREATE TABLE IF NOT EXISTS {table_name} (
      {columns_sql}
    ) {table_options};
    '''
    
    # Print the SQL for debugging
    if debug is True:
      print("Executing SQL:\n", create_table_sql)
    
    # Connect to the database and execute SQL
    # Ensure self.get_db_connection() is used to get a fresh connection
    conn = self.db_conn
    try:
      c = conn.cursor()
      c.execute(create_table_sql)
      conn.commit()
      print(f"Table '{table_name}' created/verified successfully.")
    except pymysql.Error as e:
      print(f"Error creating table '{table_name}': {e}")
      conn.rollback()
    finally:
      if conn: # Ensure connection is closed even if an error occurs
        conn.close()

class TempTester:
  def __init__(self):
    self.models_util = models.Utils(debug_mode=False)
  
  def print_db_info(self):
    conn = self.models_util.get_db_connection()
    print(conn)
    c = conn.cursor()
    
    pass
    
    conn.close()




if __name__ == '__main__':

  #initializer = Initialize(automatic_mode=True)
  a = TempTester()
  a.print_db_info()
  
