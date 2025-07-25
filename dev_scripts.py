import json
import pymysql
from flask_app import models, settings
from dotenv import load_dotenv

load_dotenv()
import speedGauge_app
from speedGauge_app import SpeedgaugeApi as sga
from speedGauge_app import analytics

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

        # establist connection to the database
        self.models_util = models.Utils(debug_mode=False)
        self.models_cli_util = models.CLI_Utils(debug_mode=False)
        self.sgProcessor = speedGauge_app.sgProcessor.Processor(self.models_util)
        self.analytics_obj = analytics.Analytics(self.models_util)

        if automatic_mode is True:
            # if this is set to true, then go ahead and just automatically run this thing.
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

        # build the database
        print("Building the Database....")
        self.models_util.build_db()

        # build the tables in the database
        print("\nCreating tables for database....")
        tables = {
            "speedGauge_data": settings.DATABASE_DIR / "speedGauge_table.json",
            "company_analytics_table": settings.DATABASE_DIR
            / "company_analytics_table.json",
            "driver_analytics_table": settings.DATABASE_DIR
            / "driver_analytics_table.json",
            "visit_log_table": settings.DATABASE_DIR / "visit_log_table.json",
        }

        for table_name, schema_path in tables.items():
            print(f"Creating table: {table_name}")
            self.create_table_from_json(json_file=schema_path, table_name=table_name)

        # Enter users from the json file
        print("\nEntering users from json file....")
        self.models_cli_util.enter_users_from_json()

        print("Database initialized successfully.\n")

        # Populate the speedGauge table with all the files we have
        print("Populating the speedGauge table...")
        self.sgProcessor.standard_flow()

    def construct_dirs(self):
        """Method to build necessary directories"""
        dirs_to_construct = [self.unprocessed_dir, self.processed_dir]

        for directory in dirs_to_construct:
            try:
                # parents=True creates parent directories if they don't exist
                # exist_ok=True prevents an error if the directory already exists
                directory.mkdir(parents=True, exist_ok=True)
                print(f"Directory ensured: {directory}")
            except OSError as e:
                print(f"Error creating directory {directory}: {e}")

    def processess_speedgauge(self):
        """stick all speedguage files into the database for initial setup"""
        self.sgProcessor.standard_flow()
        self.analytics_obj.standard_flow()
        

    def create_table_from_json(self, json_file=None, table_name=None, debug=False):

        # Load JSON data from file
        with open(json_file, "r", encoding="utf-8") as file:
            column_info = json.load(file)

        columns = []
        table_options = ""
        unique_constraints = []

        # Separate columns from table_options and unique_constraints
        if "table_options" in column_info:
            table_options = column_info.pop("table_options")

        if "unique_constraints" in column_info:
            unique_constraints = column_info.pop("unique_constraints")

        for column, definition in column_info.items():
            columns.append(f"{column} {definition}")

        # Join column definitions with proper indentation
        columns_sql = ",\n      ".join(columns)

        # Add unique constraints to the SQL statement
        if unique_constraints:
            constraints_sql = ",\n      ".join(unique_constraints)
            columns_sql += f",\n      {constraints_sql}"

        # Construct SQL CREATE TABLE statement
        # Remove quotes around table_name for MySQL compatibility
        create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
            {columns_sql}
            ) {table_options};
            """

        # Print the SQL for debugging
        if debug is True:
            print("Executing SQL:\n", create_table_sql)

        # Connect to the database and execute SQL
        conn = self.models_util.get_db_connection()
        try:
            c = conn.cursor()
            c.execute(create_table_sql)
            conn.commit()
            print(f"Table '{table_name}' created/verified successfully.\n")
        except pymysql.Error as e:
            print(f"Error creating table '{table_name}': {e}")
            conn.rollback()
        finally:
            if conn:  # Ensure connection is closed even if an error occurs
                conn.close()

    def run_analyitics(self):
        """Run the analytics on the speedGauge data"""
        print("Running analytics on speedGauge data...")
        self.sgProcessor.run_analytics()
        print("Analytics completed successfully.\n")


class TempTester:
    def __init__(self):
        self.models_util = models.Utils(debug_mode=False)
        self.models_cli_util = models.CLI_Utils(debug_mode=False)
        self.sgProcessor = speedGauge_app.sgProcessor.Processor(
            self.models_util, initialize=False
        )
        self.sga = sga.Api(30150643, self.models_util)

    def print_dicts(self):
        self.sgProcessor.standard_flow()

    def print_db_info(self):
        conn = self.models_util.get_db_connection()
        c = conn.cursor()
        sql = """
    SHOW DATABASES;
    """
        c.execute(sql)
        results = c.fetchall()
        for dict in results:
            print(dict)

        conn.close()

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


if __name__ == "__main__":
    print("Running dev_scripts\n**********\n\n")
    initialization = Initialize(automatic_mode=True)
