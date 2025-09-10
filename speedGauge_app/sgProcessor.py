import json
import re
import shutil
import math
from datetime import datetime
from dateutil import parser as dateparser
import pandas as pd
from flask_app import settings
from flask_app.extensions import db
from flask_app.models.speedgauge import SpeedGaugeData

class Processor:
    """This class chomps through the speedGauge csv, extracts the data, and stores it in the db using SQLAlchemy."""

    def __init__(self):
        """The Processor no longer needs a direct db connection utility.
        It will use the SQLAlchemy session from flask_app.extensions.
        """
        pass

    def standard_flow(self):
        """Method that will process the csv files in an orderly manner"""
        files = self.find_unprocessed_files()
        for csv_file in files:
            dict_list = self.extract_data(csv_file)
            date_info = self.extract_date(csv_file)

            for driver_dict in dict_list:
                driver_dict["start_date"] = date_info[0]
                driver_dict["end_date"] = date_info[1]

                parsed_names = self.parse_names(driver_dict["driver_name"])
                driver_dict["first_name"] = parsed_names[0]
                driver_dict["last_name"] = parsed_names[1]

                try:
                    driver_id = driver_dict["driver_id"]
                except KeyError:
                    driver_dict["driver_id"] = None

                try:
                    url = driver_dict["url"]
                except KeyError:
                    driver_dict["url"] = "-"

                if driver_dict["driver_id"] is None:
                    driver_num = self.locate_missing_driver_number(driver_dict)
                    driver_dict["driver_id"] = driver_num
                else:
                    self.update_drivers_json(driver_dict)

                lat, lon = self.get_lat_long(driver_dict["url"])
                driver_dict["url_lat"] = lat
                driver_dict["url_lon"] = lon

                sanitized_dict = self.sanitize_dict(driver_dict)

                # Create a copy for JSON serialization
                json_dict = sanitized_dict.copy()
                for k, v in json_dict.items():
                    if isinstance(v, datetime):
                        json_dict[k] = v.isoformat()

                driver_dict_json_string = json.dumps(json_dict)
                sanitized_dict["raw_json"] = driver_dict_json_string

                self.store_row_in_db(sanitized_dict)

            db.session.commit()
            print(f"Database changes for {csv_file.name} committed.")
            self.move_csv_to_proccessed(csv_file)

    def move_csv_to_proccessed(self, csv_file):
        destination = settings.PROCESSED_SPEEDGAUGE_PATH / csv_file.name
        shutil.move(str(csv_file), str(destination))

    def sanitize_dict(self, driver_dict):
        sanitized_dict = {}
        numeric_fields = [
            "percent_speeding", "max_speed_non_interstate_freeway",
            "percent_speeding_non_interstate_freeway", "speed_limit", "speed",
            "distance_driven", "url_lat", "url_lon", "percent_speeding_numerator",
            "percent_speeding_denominator", "max_speed_interstate_freeway",
            "percent_speeding_interstate_freeway", "incidents_interstate_freeway",
            "observations_interstate_freeway", "incidents_non_interstate_freeway",
            "observations_non_interstate_freeway", "difference",
        ]
        boolean_fields = ["is_interpolated"]
        date_fields = ["worst_incident_date", "start_date", "end_date"]

        for key, value in driver_dict.items():
            if pd.isna(value):
                value = None

            sanitized_key = re.sub(r"[-/ ]", "_", key) # Also replace spaces

            if key == "driver_id":
                try:
                    value = int(float(str(value)))
                except (ValueError, TypeError):
                    value = None
            elif key in date_fields:
                if pd.isna(value) or str(value).strip() in ["-", ""]:
                    value = None
                elif not isinstance(value, datetime):
                    try:
                        value = dateparser.parse(str(value))
                    except ValueError:
                        value = None
            elif key in boolean_fields:
                if pd.isna(value) or str(value).strip() in ["-", ""]:
                    value = None
                elif isinstance(value, str):
                    value = value.lower() == "true"
                else:
                    value = bool(value)
            elif key in numeric_fields:
                if pd.isna(value) or str(value).strip() in ["-", ""]:
                    value = None
                elif isinstance(value, str):
                    try:
                        value = float(value)
                    except ValueError:
                        value = None
            
            sanitized_dict[sanitized_key] = value

        return sanitized_dict

    def store_row_in_db(self, driver_dict):
        existing_row = self.chk_row_exists(
            driver_dict.get("driver_id"),
            driver_dict.get("start_date"),
            driver_dict.get("end_date")
        )

        if existing_row:
            self.update_row_in_db(existing_row, driver_dict)
        else:
            self.enter_row_into_db(driver_dict)

    def update_row_in_db(self, existing_row, driver_data):
        """Updates an existing SQLAlchemy row object with new data."""
        for key, value in driver_data.items():
            # Ensure the key exists as an attribute on the model before setting
            if hasattr(existing_row, key):
                setattr(existing_row, key, value)
        print(f"Updating row for driver {existing_row.driver_id} on {existing_row.start_date}")

    def enter_row_into_db(self, driver_data):
        """Creates a new SpeedGaugeData record and adds it to the session."""
        # Filter out keys from driver_data that are not in the SpeedGaugeData model
        valid_keys = [c.name for c in SpeedGaugeData.__table__.columns]
        filtered_data = {k: v for k, v in driver_data.items() if k in valid_keys}

        new_row = SpeedGaugeData(**filtered_data)
        db.session.add(new_row)
        print(f"Adding new row for driver {new_row.driver_id} on {new_row.start_date}")

    def chk_row_exists(self, driver_id, start_date, end_date):
        """Checks if a row of data already exists using SQLAlchemy."""
        if not all([driver_id, start_date, end_date]):
            return None
        return db.session.query(SpeedGaugeData).filter_by(
            driver_id=driver_id,
            start_date=start_date,
            end_date=end_date
        ).first()

    def parse_names(self, name_str):
        cleaned_name = name_str.strip()
        name_parts = cleaned_name.split()
        if not name_parts:
            return None, None
        elif len(name_parts) == 1:
            return name_parts[0], None
        else:
            return name_parts[0], name_parts[-1]

    def get_lat_long(self, url):
        pattern = r"la=(-?\d+\.\d+)&lo=(-?\d+\.\d+)&"
        match = re.search(pattern, url)
        if match:
            return float(match.group(1)), float(match.group(2))
        else:
            return None, None

    def find_unprocessed_files(self):
        file_list = []
        for file in settings.UNPROCESSED_SPEEDGAUGE_PATH.iterdir():
            if file.is_file():
                file_list.append(file)
        return file_list

    def extract_date(self, csv_file):
        df = pd.read_csv(csv_file)
        try:
            separator_index = df[df.iloc[:, 0] == "---"].index[0]
            date_range = df.iloc[separator_index + 3, 0]
            date_pattern = r"(\w+, \w+ \d{1,2}, \d{4}, \d{2}:\d{2})"
            matches = re.findall(date_pattern, date_range)
            if len(matches) == 2:
                date_format = "%A, %B %d, %Y, %H:%M"
                start_date_obj = datetime.strptime(matches[0], date_format)
                end_date_obj = datetime.strptime(matches[1], date_format)
                return start_date_obj, end_date_obj
            else:
                raise ValueError("Date string format did not match expected pattern.")
        except (IndexError, ValueError) as e:
            print(f"Could not extract date from {csv_file.name}: {e}")
            # Return a default or handle as appropriate
            return None, None

    def extract_data(self, csv_file):
        df = pd.read_csv(csv_file)
        dict_list = []
        try:
            separator_index = df[df.iloc[:, 0] == "---"].index[0]
            data_df = df.iloc[:separator_index]
            for index, row in data_df.iterrows():
                driver_name = str(row.get("driver_name", ""))
                if driver_name and driver_name.lower() != 'median' and not driver_name[0].isdigit():
                    dict_list.append(row.to_dict())
        except IndexError:
            print(f"Could not find separator '---' in {csv_file.name}. Reading all rows.")
            # Fallback to reading the whole file if separator is not found
            dict_list = df.to_dict('records')
        return dict_list

    def update_drivers_json(self, drivers_dict):
        driver_num = drivers_dict.get("driver_id")
        first_name = drivers_dict.get("first_name")
        last_name = drivers_dict.get("last_name")
        if not all([driver_num, first_name, last_name]):
            return

        driver_info_dict = {
            "driver_id": driver_num,
            "first_name": first_name,
            "last_name": last_name,
        }
        json_file = settings.DATABASE_DIR / "drivers.json"
        try:
            with open(json_file, "r+", encoding="utf-8") as f:
                json_dict_list = json.load(f)
                if not any(d["driver_id"] == driver_num for d in json_dict_list):
                    json_dict_list.append(driver_info_dict)
                    f.seek(0)
                    json.dump(json_dict_list, f, indent=4)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error updating drivers.json: {e}")

    def locate_missing_driver_number(self, driver_dict):
        first_name = driver_dict.get("first_name")
        last_name = driver_dict.get("last_name")
        if not all([first_name, last_name]):
            return None

        drivers_json = settings.DATABASE_DIR / "drivers.json"
        try:
            with open(drivers_json, "r", encoding="utf-8") as file:
                drivers_list = json.load(file)
                for driver in drivers_list:
                    if (
                        driver.get("first_name", "").lower() == first_name.lower()
                        and driver.get("last_name", "").lower() == last_name.lower()
                    ):
                        return driver.get("driver_id")
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error locating driver number from JSON: {e}")
        return None