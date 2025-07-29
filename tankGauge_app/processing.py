from pathlib import Path
from rich.traceback import install
import pandas as pd
from sqlalchemy import or_
from dbConnector import fetch_session
from .models import StoreData
import numpy as np # Import numpy for pd.isna
install()

class Processing:
    def __init__(self):
        # establish paths to the excel files we want to insert into database
        self.tankGauge_files = Path('tankGauge_app/tankGauge_files')
        self.charts_dir = self.tankGauge_files / 'tank_charts'
        self.misc_dir = self.tankGauge_files / 'misc'

    def store_data_entry(self):
        """
        Reads store data from 'storeInfo_master.xlsx', and performs an upsert
        (update or insert) into the StoreData table based on 'store_num' OR 'riso_num'.
        """
        excel_file = self.misc_dir / 'storeInfo_master.xlsx'

        if not excel_file.exists():
            print(f"Error: Expected Excel file not found: {excel_file}")
            print("Please ensure 'storeInfo_master.xlsx' exists in the specified directory.")
            return

        try:
            # Read the Excel file directly
            # Requires 'openpyxl' to be installed (pip install openpyxl)
            df = pd.read_excel(excel_file)
        except Exception as e:
            print(f"Error reading Excel file {excel_file.name}: {e}")
            print("Ensure 'openpyxl' is installed (pip install openpyxl) and the file is valid.")
            return

        session = next(fetch_session()) # Get a new database session
        inserted_count = 0
        updated_count = 0

        try:
            # Iterate through each row of the DataFrame
            for index, row in df.iterrows():
                # Get identifying data from the row.
                current_store_num = row.get('store_num')
                current_riso_num = row.get('riso_num')

                # set NaN values to None for db insertion
                if pd.isna(current_store_num): # Check if it's NaT or NaN
                    current_store_num = None
                
                if pd.isna(current_riso_num): # Check if it's NaT or NaN
                    current_riso_num = None

                # Skip row if both identifying numbers are missing
                if current_store_num is None and current_riso_num is None:
                    print(f"  Skipping row {index} due to missing 'store_num' and 'riso_num'.")
                    continue

                # Build the OR condition for querying
                conditions = []
                if current_store_num is not None:
                    conditions.append(StoreData.store_num == current_store_num)
                if current_riso_num is not None:
                    conditions.append(StoreData.riso_num == current_riso_num)

                # Query to find an existing store by either identifier
                existing_store = session.query(StoreData).filter(or_(*conditions)).first()

                # Prepare common data fields from the row
                # Use .get() for robustness, providing None as default if column missing
                # Ensure 'install_date' is converted to a date object if your DB column is DATE
                raw_install_date_val = row.get('install_date')
                install_date_val = None # Default to None

                if pd.isna(raw_install_date_val): # Check if it's NaT or NaN
                    install_date_val = None
                elif isinstance(raw_install_date_val, pd.Timestamp):
                    install_date_val = raw_install_date_val.date()
                
                # Handle zip (string to int or None, remove hyphens if present)
                raw_zip_val = row.get('zip')
                zip_val = None
                if not pd.isna(raw_zip_val):
                    try:
                        # Remove any non-digit characters before converting to int
                        cleaned_zip = str(raw_zip_val).split('-')[0].strip() # Take only the first part before hyphen
                        zip_val = int(cleaned_zip)
                    except (ValueError, TypeError):
                        print(f"  Warning: Could not convert 'zip' value '{raw_zip_val}' to integer at row {index}. Setting to None.")
                        zip_val = None

                # Handle lat (to float or None)
                raw_lat_val = row.get('lat')
                lat_val = None
                if not pd.isna(raw_lat_val):
                    try:
                        lat_val = float(raw_lat_val)
                    except (ValueError, TypeError):
                        print(f"  Warning: Could not convert 'lat' value '{raw_lat_val}' to float at row {index}. Setting to None.")
                        lat_val = None

                # Handle lon (to float or None)
                raw_lon_val = row.get('lon')
                lon_val = None
                if not pd.isna(raw_lon_val):
                    try:
                        lon_val = float(raw_lon_val)
                    except (ValueError, TypeError):
                        print(f"  Warning: Could not convert 'lon' value '{raw_lon_val}' to float at row {index}. Setting to None.")
                        lon_val = None
                
                store_data = {
                    'store_num': current_store_num,
                    'riso_num': current_riso_num,
                    'store_name': row.get('store_name'),
                    'store_type': row.get('store_type'),
                    'address': row.get('address'),
                    'city': row.get('city'),
                    'state': row.get('state'),
                    'zip': zip_val,
                    'lat': lat_val,
                    'lon': lon_val,
                    'install_date': install_date_val,
                    'overfill_protection': row.get('overfill_protection')
                }

                # Check for null values in pandas dataframe data.
                # Convert to None for db insertion.
                for key, value in store_data.items(): # Iterate through key-value pairs
                    if pd.isna(value): # Use pd.isna() to check for NaN, NaT, and None
                        store_data[key] = None # <--- Corrected assignment

                if existing_store:
                    # If store exists, update its attributes
                    row_actually_updated = False
                    for key, value in store_data.items():
                        if key != 'id': # Always skip 'id'
                            # Check if value is different OR if incoming value is None and existing is not (to allow setting to NULL)
                            # Or if you want to allow setting to None, and existing is not None
                            if value is not None and getattr(existing_store, key) != value:
                                setattr(existing_store, key, value)
                                row_actually_updated = True
                            elif value is None and getattr(existing_store, key) is not None:
                                setattr(existing_store, key, None)
                                row_actually_updated = True

                    if row_actually_updated:
                        updated_count += 1

                else:
                    # If store does not exist, create a new record
                    new_store = StoreData(**store_data) # Create new object from dict
                    session.add(new_store)
                    inserted_count += 1

            session.commit() # Commit all changes (inserts and updates) at once

        except Exception as e:
            session.rollback() # Rollback all changes if any error occurs during the process
            print(f"An error occurred during store data entry: {e}")
        finally:
            session.close() # Always close the session

    def tank_chart_entry(self):
        pass

    def tank_data_entry(self):
        pass

    def store_tank_map(self):
        pass
