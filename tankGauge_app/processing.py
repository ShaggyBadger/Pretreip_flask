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

    def store_data_entry2(self):
        file = self.misc_dir / 'storeInfo_master.xlsx'
        df = pd.read_excel(file)

        session = next(fetch_session())
        try:
            stores_to_add = []
            for _, row in df.iterrows():
                stores_to_add.append(StoreData(
                    store_num=row['store_num'],
                    riso_num=row['riso_num'],
                    store_name=row['store_name'],
                    store_type=row['store_type'],
                    address=row['address'],
                    city=row['city'],
                    state=row['state'],
                    zip=row['zip'],
                    lat=row['lat'],
                    lon=row['lon'],
                    install_date=row['install_date'],
                    overfill_protection=row['overfill_protection']
                ))

            if stores_to_add:
                session.bulk_save_objects(stores_to_add)
                session.commit()
                print(f"Successfully inserted {len(stores_to_add)} new store records.")

        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")
        finally:
            session.close()
    
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

                # Skip row if both identifying numbers are missing
                if current_store_num is None and current_riso_num is None:
                    print(f"  Skipping row {index} due to missing 'store_num_col' and 'riso_num_col'.")
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
                # Ensure 'install_date_col' is converted to a date object if your DB column is DATE
                raw_install_date_val = row.get('install_date')
                install_date_val = None # Default to None

                if pd.isna(raw_install_date_val): # Check if it's NaT or NaN
                    install_date_val = None
                elif isinstance(raw_install_date_val, pd.Timestamp):
                    install_date_val = raw_install_date_val.date()
                
                store_data = {
                    'store_num': current_store_num,
                    'riso_num': current_riso_num,
                    'store_name': row.get('store_name_col'),
                    'store_type': row.get('store_type_col'),
                    'address': row.get('address_col'),
                    'city': row.get('city_col'),
                    'state': row.get('state_col'),
                    'zip': row.get('zip_col'),
                    'lat': row.get('lat_col'),
                    'lon': row.get('lon_col'),
                    'install_date': install_date_val,
                    'overfill_protection': row.get('overfill_protection_col')
                }

                if existing_store:
                    # If store exists, update its attributes
                    for key, value in store_data.items():
                        # Only update if the incoming value is not None (or if you want to allow None updates)
                        # Also, avoid updating primary key 'id' or other non-updatable fields if they were in store_data
                        if value is not None and key != 'id':
                            setattr(existing_store, key, value)
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
