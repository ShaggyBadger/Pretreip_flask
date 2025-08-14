import json
from dotenv import load_dotenv
load_dotenv()
import speedGauge_app
from speedGauge_app import SpeedgaugeApi as sga
from speedGauge_app import analytics

from flask_app import settings
from flask_app.utils import Utils, CLI_Utils
from flask_app.app_constructor import app # Import app instance
from flask_app.models.users import Users # Import Users model here
from flask_app.models.tankgauge import StoreData, TankData, TankCharts, StoreTankMap
from flask_app.extensions import db

from tankGauge_app.initialization_processing import Processing

from rich.traceback import install
from rich import print

install()


class Initialize:
    """
    Class used to initialize the project
    """

    def __init__(self, automatic_mode=False):
        # Define the base directory for speedGauge files
        self.speedgauge_base_dir = settings.SPEEDGAUGE_DIR
        self.processed_dir = settings.PROCESSED_SPEEDGAUGE_PATH
        self.unprocessed_dir = settings.UNPROCESSED_SPEEDGAUGE_PATH

        # Initialize utilities
        self.models_util = Utils(debug_mode=False)
        self.models_cli_util = CLI_Utils(debug_mode=False)
        self.sgProcessor = speedGauge_app.sgProcessor.Processor(self.models_util)
        self.analytics_obj = analytics.Analytics(self.models_util)

        if automatic_mode is True:
            self.standard_flow()

    def standard_flow(self):
        """General controller method that will automatically flow through and set everything up"""
        self.construct_dirs()
        self.initialize_db()
        self.processess_speedgauge()

    def initialize_db(self):
        """automated database creation. This will populate the users table with all the id's from my
        company. Later on anyone can register to use the program as well."""
        print("Initializing the database...")

        # Enter users from the json file
        print("\nEntering users from json file....")
        # This part needs to be called with an app context, but the app is not available here
        # This class is for general initialization, not specific app context tasks. 
        # The repopulate_users_from_json function below handles the app context.
        # self.models_cli_util.enter_users_from_json()

        print("Database initialized successfully.\n")

        # Populate the speedGauge table with all the files we have
        print("Populating the speedGauge table...")
        self.sgProcessor.standard_flow()

    def construct_dirs(self):
        """Method to build necessary directories"""
        dirs_to_construct = [self.unprocessed_dir, self.processed_dir]

        for directory in dirs_to_construct:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                print(f"Directory ensured: {directory}")
            except OSError as e:
                print(f"Error creating directory {directory}: {e}")

    def processess_speedgauge(self):
        """stick all speedguage files into the database for initial setup"""
        self.sgProcessor.standard_flow()
        self.analytics_obj.standard_flow()


    def run_analyitics(self):
        """Run the analytics on the speedGauge data"""
        print("Running analytics on speedGauge data...")
        self.sgProcessor.run_analytics()
        print("Analytics completed successfully.\n")

class TempTester:
    def __init__(self):
        self.models_util = Utils(debug_mode=False)
        self.models_cli_util = CLI_Utils(debug_mode=False)
        self.sgProcessor = speedGauge_app.sgProcessor.Processor(
            self.models_util, initialize=False
        )
        self.sga = sga.Api(30150643, self.models_util)

    def print_dicts(self):
        self.sgProcessor.standard_flow()

    def print_db_info(self):
        # This method needs to be refactored to use SQLAlchemy if needed.
        # For now, it's commented out as it uses raw SQL.
        print("print_db_info is not implemented with SQLAlchemy yet.")
        pass

    def test_api(self):
        a = self.sga.build_speedgauge_report()

        print("\nStarting devscript report on sg api query results\n*******")
        print(type(a))
        print(a)
        print("\n********")
        for i in a:
            print(i)

    def reload_processed_csv(self):
        file_list = []

        for file in settings.PROCESSED_SPEEDGAUGE_PATH.iterdir():
            if file.is_file():
                file_list.append(file)

        for file in file_list:
            date_tuple = self.sgProcessor.extract_date(file)
            for d in date_tuple:
                print(f"type: {type(d)}")
                print(f"value: {d}")
                print("")
            print("******\n")

class tankGauge_control:
    def __init__(self):
        # init_db() is no longer needed with Flask-SQLAlchemy
        self.processing_obj = Processing()
    
    def initialize(self):
        self.run_store_data()
        self.run_tank_data()
        self.run_charts_data()
        self.run_store_tank_map()
    
    def run_store_data(self):
        self.processing_obj.store_data_entry()

    def run_tank_data(self):
        self.processing_obj.tank_data_entry()
    
    def run_charts_data(self):
        self.processing_obj.tank_chart_entry()
    
    def run_store_tank_map(self):
        self.processing_obj.store_tank_map()

def repopulate_users_from_json():
    print("Running repopulate_users_from_json...")
    # Get the app instance
    
    with app.app_context(): # USE the globally imported 'app'
        cli_utils = CLI_Utils()
        
        print("Clearing existing users table...")
        cli_utils.clear_users()
        print("Users table cleared.")
        
        print("Re-entering users from JSON file...")
        cli_utils.enter_users_from_json()
        print("Users re-entered from JSON.")
        
        # Optional: Verify the count and a sample user
        print(f"Total users in DB: {Users.query.count()}")
        print(f"First user in DB: {Users.query.first()}")

def reinitialize_tank_gauge_tables():
    print("Re-initializing tank gauge tables...")
    with app.app_context():
        try:
            print("Dropping tank gauge tables...")
            db.session.query(StoreTankMap).delete()
            db.session.query(TankCharts).delete()
            db.session.query(TankData).delete()
            db.session.query(StoreData).delete()
            db.session.commit()
            print("Tank gauge tables dropped.")
        except Exception as e:
            db.session.rollback()
            print(f"Error dropping tables: {e}")
            return

        print("Repopulating tank gauge tables...")
        tank_gauge_controller = tankGauge_control()
        tank_gauge_controller.initialize()
        print("Tank gauge tables repopulated.")

if __name__ == "__main__":
    print("Running dev_scripts\n**********\n\n")
    # initialization = Initialize(automatic_mode=True) 
    # tankGauge_controler = tankGauge_control()
    # tankGauge_controler.initialize()

    # Call the new function to repopulate users
    # repopulate_users_from_json()
    # reinitialize_tank_gauge_tables()