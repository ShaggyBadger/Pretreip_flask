import pymysql
import json
import re
import shutil
import math
from datetime import datetime
from dateutil import parser as dateparser
import pandas as pd
from flask_app import settings
from speedGauge_app import analytics


class Processor:
    """This class chomps through the speedGauge csv, extracts the data, and stores it in db"""

    def __init__(self, models_utils):
        """Remember to go back in here and delete the build_speedgauge_table method
        and the tbl_col_names attribute. We dont need them anymore."""
        # make sure to send models util object here so we can get db connection
        self.models_utils = models_utils
        self.tbl_col_names = self.get_columns_in_table()
        self.analytics_obj = analytics.Analytics(self.models_utils)
        self.analytics_obj.standard_flow()
        # if initialize is True:
        #     # make sure table is built
        #     self.build_speedgauge_table()

        #     # get some useful data together
        #     self.tbl_col_names = self.get_columns_in_table()

    def standard_flow(self):
        """Method that will process the csv files in an orderly manner"""
        files = self.find_unprocessed_files()
        for csv_file in files:
            # build list  of dictionaries. each dict one row of csv
            dict_list = self.extract_data(csv_file)

            # build date info from the csv and attach it to the dictionary for each row
            date_info = self.extract_date(csv_file)
            for driver_dict in dict_list:
                # insert the dates
                driver_dict["start_date"] = date_info[0]
                driver_dict["end_date"] = date_info[1]

                # fix the names. Isolate the first and last name, and attach that  to the dictionary
                parsed_names = self.parse_names(driver_dict["driver_name"])
                driver_dict["first_name"] = parsed_names[0]
                driver_dict["last_name"] = parsed_names[1]

                # if driver_dict is missing driver_number, run this to find it and add driver_num to dict

                # first, set driver id to None if its one of those csv file with no driver ids
                try:
                    driver_id = driver_dict["driver_id"]
                except:
                    driver_dict["driver_id"] = None

                try:
                    url = driver_dict["url"]
                except:
                    driver_dict["url"] = "-"

                # then find the id
                if driver_dict["driver_id"] is None:
                    driver_num = self.locate_missing_driver_number(driver_dict)
                    driver_dict["driver_id"] = driver_num
                else:
                    # send to json file to make sure driver is listed there
                    # this doesnt actually need to be in this if/else statement
                    # but i like it so whatever
                    self.update_drivers_json(driver_dict)

                # add coords of url
                lat, lon = self.get_lat_long(driver_dict["url"])
                driver_dict["url_lat"] = lat
                driver_dict["url_lon"] = lon

                # sanitize the dict
                sanitized_dict = self.sanitize_dict(driver_dict)

                # add raw_json of all this stuff to the dict
                # Convert datetime objects to string for JSON serialization
                for k, v in sanitized_dict.items():
                    if isinstance(v, datetime):
                        sanitized_dict[k] = v.isoformat()

                driver_dict_json_string = json.dumps(sanitized_dict)
                sanitized_dict["raw_json"] = driver_dict_json_string

                # final step! everything is cleaned up and processed. Now
                # send it to the database for storage
                self.store_row_in_db(sanitized_dict)

                # i guess the actual final step is to run the analytics and store that in db as well
                pass

            self.move_csv_to_proccessed(csv_file)

    def move_csv_to_proccessed(self, csv_file):
        """Moves the csv file around"""
        # make a destination path object
        destination = settings.PROCESSED_SPEEDGAUGE_PATH / csv_file.name

        # use shutil to move the file
        shutil.move(str(csv_file), str(destination))

    def build_speedgauge_table(self):
        """ensures the table is created for our data"""
        # get data from json file
        with open(settings.SPEEDGAUGE_DIR / "speedGauge_table.json", "r") as f:
            table_schema_dict = json.load(f)

        conn = self.models_utils.get_db_connection()
        c = conn.cursor()

        table_name = settings.speedGuage_data_tbl_name

        # Extract table options before processing columns
        table_options = table_schema_dict.pop("table_options", "")

        columns_sql = ",\n    ".join(
            f"{column} {data_type}" for column, data_type in table_schema_dict.items()
        )
        create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS  {table_name} (
      {columns_sql}
    ) {table_options};
    """

        c.execute(create_table_sql)
        conn.commit()
        conn.close()

    def sanitize_dict(self, driver_dict):
        """cleans up the info to prepare for database insertion"""
        sanitized_dict = {}

        # Define numeric and boolean fields based on your schema for robust handling
        numeric_fields = [
            "percent_speeding",
            "max_speed_non_interstate_freeway",
            "percent_speeding_non_interstate_freeway",
            "speed_limit",
            "speed",
            "distance_driven",
            "url_lat",
            "url_lon",
            "percent_speeding_numerator",
            "percent_speeding_denominator",
            "max_speed_interstate_freeway",
            "percent_speeding_interstate_freeway",
            "incidents_interstate_freeway",
            "observations_interstate_freeway",
            "incidents_non_interstate_freeway",
            "observations_non_interstate_freeway",
            "difference",
        ]
        boolean_fields = ["is_interpolated"]
        date_fields = ["worst_incident_date", "start_date", "end_date"]

        for key, value in driver_dict.items():
            # Convert NaN to None for any field first
            if pd.isna(value):
                value = None

            # Sanitize key (column name)
            sanitized_key = re.sub(r"[-/]", "_", key)

            # Handle driver_id specifically as it's an INT
            if key == "driver_id":
                try:
                    value = int(float(str(value)))  # Robust conversion to int
                except (ValueError, TypeError):
                    value = None  # Set to None if conversion fails

            # Handle date fields
            elif key in date_fields:
                if (
                    pd.isna(value)
                    or str(value).strip() == "-"
                    or str(value).strip() == ""
                ):
                    value = None  # Convert to None for NULL in database
                elif not isinstance(value, datetime):
                    # Attempt to parse the date string if it's not None
                    try:
                        # Assuming the format is 'MM/DD/YYYY HH:MM'
                        value = dateparser.parse(str(value))
                    except ValueError:
                        # If parsing fails, set to None or handle as appropriate
                        print(f"Date parsing failed for key '{key}': {value}")
                        input(
                            "press enter to continue. this is the value=dateparser portion. setting date to None"
                        )
                        value = None

            # Handle boolean fields
            elif key in boolean_fields:
                if (
                    pd.isna(value)
                    or str(value).strip() == "-"
                    or str(value).strip() == ""
                ):
                    value = None
                elif isinstance(value, str):
                    value = (
                        value.lower() == "true"
                    )  # Convert 'True'/'False' strings to boolean
                else:
                    value = bool(value)  # Convert other types to boolean (e.g., 0/1)

            # Handle numeric fields
            elif key in numeric_fields:
                if (
                    pd.isna(value)
                    or str(value).strip() == "-"
                    or str(value).strip() == ""
                ):
                    value = None
                elif isinstance(value, str):
                    try:
                        # Attempt conversion to float first, then int if applicable
                        if "." in value:  # Heuristic for float
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        value = None  # If conversion fails, set to None
                # If it's already a number (int/float), keep it as is.

            # build the dict entry
            sanitized_dict[sanitized_key] = value

        return sanitized_dict

    def store_row_in_db(self, driver_dict):
        """stores row into the database"""
        # update db with any new columns
        dict_keys = [key for key in driver_dict]

        for k in dict_keys:
            if k not in self.tbl_col_names:
                self.add_col(k)

        # check if this row already exists
        driver_id = driver_dict["driver_id"]
        start_date = driver_dict["start_date"]
        end_date = driver_dict["end_date"]

        if self.chk_row_exists(driver_id, start_date, end_date):
            # if exists, then update row
            self.update_row_in_db(driver_dict)
        else:
            # if doesnt exist, just add row
            self.enter_row_into_db(driver_dict)

    def add_col(self, column_name):
        """Adds a column to the database if there is a new column in the speedgauge CSV that does not have a
        corresopnding column in my database. Default to TEXT and i can clean it up in processing later
        """
        conn = self.models_utils.get_db_connection()
        c = conn.cursor()

        sql = f"""
    ALTER TABLE {settings.speedGuage_data_tbl_name}
    ADD COLUMN {column_name} TEXT
    """
        c.execute(sql)
        conn.commit()
        conn.close()

    def update_row_in_db(self, driver_dict):
        """updates an existing row with fresh (possible more accurate) data"""
        conn = self.models_utils.get_db_connection()
        c = conn.cursor()

        # Create a copy to modify without affecting the original dict
        sanitized_driver_data = {}
        for k, v in driver_dict.items():
            if isinstance(v, float) and math.isnan(v):
                sanitized_driver_data[k] = None  # Replace NaN with None
            else:
                sanitized_driver_data[k] = v

        # Prepare the SET part of the SQL statement
        set_clause = ", ".join([f"{key} = %s" for key in sanitized_driver_data.keys()])

        # Prepare the values for the SET part and the WHERE part
        values = list(sanitized_driver_data.values())
        values.extend(
            [
                sanitized_driver_data["driver_id"],
                sanitized_driver_data["start_date"],
                sanitized_driver_data["end_date"],
            ]
        )

        sql = f"""
    UPDATE {settings.speedGuage_data_tbl_name}
    SET {set_clause}
    WHERE driver_id = %s AND start_date = %s AND end_date = %s
    """

        try:
            c.execute(sql, tuple(values))
            conn.commit()
        except pymysql.Error as e:
            print(f"Error updating row: {e}")
            conn.rollback()
        finally:
            conn.close()

    def enter_row_into_db(self, driver_data):
        """Enters driver data row into the database"""
        # Create a copy to modify without affecting the original dict if it's used elsewhere
        sanitized_driver_data = {}
        for k, v in driver_data.items():
            if isinstance(v, float) and math.isnan(v):
                sanitized_driver_data[k] = None  # Replace NaN with None
            else:
                sanitized_driver_data[k] = v
        columns = ", ".join(sanitized_driver_data.keys())
        placeholders = ", ".join(["%s"] * len(sanitized_driver_data))
        values = tuple(sanitized_driver_data.values())

        sql = f"INSERT INTO {settings.speedGuage_data_tbl_name} ({columns}) VALUES ({placeholders})"

        conn = self.models_utils.get_db_connection()
        c = conn.cursor()
        try:
            c.execute(sql, values)
        except Exception as e:  # Catch the specific exception
            print(f"Error inserting row: {e}")  # Print the actual error
            # You can still print values for debugging if needed, but the 'e' is key
            # for i in values:
            #   print(f'{i}\n{type(i)}\n\n')
            user_input = input(
                'pausing due to error. Enter "y" to get info on the insertion: '
            )  # Better message for clarity
            if user_input == "y":
                print(f"SQL: {sql}")
                print(f"Values: {values}")
                print(f"Driver Data: {sanitized_driver_data}")
                print(f"Error: {e}")
                input("Press Enter to continue...")
        conn.commit()
        conn.close()

    def chk_row_exists(self, driver_id, start_date, end_date):
        """Checks if a row of data already exists in the database"""
        conn = self.models_utils.get_db_connection()
        c = conn.cursor()

        sql = f"""
    SELECT *
    FROM {settings.speedGuage_data_tbl_name}
    WHERE
      driver_id = %s
      AND start_date = %s
      AND end_date = %s
    """
        values = (driver_id, start_date, end_date)
        c.execute(sql, values)
        result = c.fetchone()
        conn.close()

        if result:
            return True
        else:
            return False

    def get_columns_in_table(self):
        """Returns a list of column names in database table"""
        conn = self.models_utils.get_db_connection()
        c = conn.cursor()

        sql = '''
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = "pretrip_db"
            AND TABLE_NAME = "speedGauge_data";
            '''
        c.execute(sql)
        results = c.fetchall()
        column_names = [row['COLUMN_NAME'] for row in results]
        conn.close()

        return column_names

    def parse_names(self, name_str):
        """This takes string with full name and returns just first and last name"""
        # strip extra white spaces
        cleaned_name = name_str.strip()

        # break name into parts
        name_parts = cleaned_name.split()

        # Handle edge cases
        if not name_parts:
            return None, None  # Empty string or only whitespace
        elif len(name_parts) == 1:
            return name_parts[0], None  # Only one name provided
        else:
            first_name = name_parts[0]
            last_name = name_parts[-1]
            return first_name, last_name

    def get_lat_long(self, url):
        """
        Extracts latitude and longitude coordinates from a given URL string.

        The function searches for latitude (`la=`) and longitude (`lo=`) parameters
        in the URL and returns them as a tuple of floats. If no match is found, it returns None.

        Parameters:
          url (str): The URL containing latitude and longitude values.

        Returns:
          tuple[float, float] | None: A tuple (latitude, longitude) if found, otherwise None.

        Example:
          >>> get_lat_long("https://example.com?la=35.827877&lo=-80.860069&")

          (35.827877, -80.860069
        """
        pattern = r"la=(-?\d+\.\d+)&lo=(-?\d+\.\d+)&"
        match = re.search(pattern, url)

        if match:
            lat = float(match.group(1))
            long = float(match.group(2))
            return lat, long

        else:
            return None, None

    def find_unprocessed_files(self):
        """
        returns a list of all files in the unprocessed folder
        """
        file_list = []

        for file in settings.UNPROCESSED_SPEEDGAUGE_PATH.iterdir():
            if file.is_file():
                file_list.append(file)

        return file_list

    def extract_date(self, csv_file):
        """
        This method locates the date in the csv and converts it to a datetime object.
        """
        df = pd.read_csv(csv_file)
        # Find the index of the row with '---'
        separator_index = df[df.iloc[:, 0] == "---"].index[0]

        # Date is 3ish rows below the
        # separator
        date_range = df.iloc[separator_index + 3, 0]

        # Define a regex to capture the two date components
        date_pattern = r"(\w+, \w+ \d{1,2}, \d{4}, \d{2}:\d{2})"
        matches = re.findall(date_pattern, date_range)

        if len(matches) == 2:
            # Parse the matched date strings
            start_date_str, end_date_str = matches

            # Define the format matching the date string
            date_format = "%A, %B %d, %Y, %H:%M"

            # Convert to datetime objects
            start_date_obj = datetime.strptime(start_date_str, date_format)
            end_date_obj = datetime.strptime(end_date_str, date_format)
            start_date = start_date_obj
            end_date = end_date_obj

            return start_date, end_date, start_date_str, end_date_str

        else:
            raise ValueError("Date string format did not match expected pattern.")
            input("Press any key to continue....")

    def extract_data(self, csv_file):
        """Pulls the data from the csv. Takes each row and makes a dictionary, then stores the dictionaries
        in a list. The list is what gets returned by this method"""
        df = pd.read_csv(csv_file)

        # make list to hold dictionaries
        dict_list = []

        # convert rows to dictionaries
        for index, row in df.iterrows():
            row_dict = row.to_dict()
            driver_name = row_dict["driver_name"]

            # break once we get to this part
            # of spreadsheet
            if driver_name == "---":
                break

            valid_name = True

            if driver_name == "median":
                valid_name = False

            if driver_name[0].isdigit():
                valid_name = False

            if valid_name is True:
                dict_list.append(row_dict)

        return dict_list

    def update_drivers_json(self, drivers_dict):
        """i have no idea what we are doing here. Probably updating the json file with any new driver info we
        might find from week to week"""
        driver_num = drivers_dict["driver_id"]
        first_name = drivers_dict["first_name"]
        last_name = drivers_dict["last_name"]

        # put into dict for json file insertion if needed
        driver_info_dict = {
            "driver_id": driver_num,
            "first_name": first_name,
            "last_name": last_name,
        }

        json_file = settings.DATABASE_DIR / "drivers.json"
        driver_in_json_file = False

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                json_dict_list = json.load(f)
        except:
            print("Couldnt open json file")

        for dict in json_dict_list:
            if dict["driver_id"] == driver_num:
                driver_in_json_file = True

        if driver_in_json_file is False:
            json_dict_list.append(driver_info_dict)

            try:
                with open(json_file, "w") as f:
                    json.dump(json_dict_list, f, indent=4)
            except:
                print(
                    f"idk. something went wrong adding this to the json file:\n{driver_info_dict}"
                )

    def locate_missing_driver_number(self, driver_dict):
        """search through the driver_info table and locate driver number based on driver_name?"""
        first_name = driver_dict["first_name"]
        last_name = driver_dict["last_name"]

        drivers_json = settings.DATABASE_DIR / "drivers.json"
        try:
            with open(drivers_json, "r", encoding="utf-8") as file:
                drivers_list = json.load(file)
                for driver in drivers_list:
                    if (
                        driver["first_name"].lower() == first_name.lower()
                        and driver["last_name"].lower() == last_name.lower()
                    ):
                        driver_number = driver["driver_id"]
                        return driver_number
        except:
            print("Unable to get this driver info for some reason")
            return None
