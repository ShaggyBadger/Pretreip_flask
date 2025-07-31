from pathlib import Path
from rich.traceback import install
import pandas as pd
from sqlalchemy import or_
from dbConnector import fetch_session
from .models import StoreData, TankData, TankCharts, StoreTankMap
import numpy as np # Import numpy for pd.isna
install()

class Processing:
    def __init__(self):
        # establish paths to the excel files we want to insert into database
        self.tankGauge_files = Path('tankGauge_app/tankGauge_files')
        self.charts_dir = self.tankGauge_files / 'tank_charts'
        self.misc_dir = self.tankGauge_files / 'misc'

        # Create the directories if they don't exist
        self.tankGauge_files.mkdir(parents=True, exists_ok=True)
        self.charts_dir.mkdir(parents=True, exist_ok=True)
        self.misc_dir.mkdir(parents=True, exist_ok=True)

    def get_session(self):
        return next(fetch_session())

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
        session = self.get_session() # Get a new database session
        chart_files = list(self.charts_dir.glob('*.xlsx'))
        try:
            for chart_file in chart_files:
                df = pd.read_excel(chart_file)
                df_columns = list(df.columns)
                row_dicts = []

                for _, row in df.iterrows():
                    row_dict = {}
                    valid_row = True

                    for col in df_columns:
                        value = row.get(col)
                        if pd.isna(value) is True:
                            # skip this entry. Something is off with the tank chart
                            valid_row = False
                        
                        row_dict[col] = value

                    if valid_row:
                        row_dicts.append(row_dict)
                
                # take all those row_dicts and insert each dict into the database
                for row in row_dicts:
                    # check to see if this chart entry is already in db
                    query = session.query(TankCharts)
                    query = query.filter(TankCharts.gallons == row.get('gallons'))
                    query = query.filter(TankCharts.inches == row.get('inches'))
                    query = query.filter(TankCharts.tank_name == row.get('tank_name'))
                    chart_entry = query.first()
                    
                    if chart_entry is None:
                        # fetch the foreign key
                        query = session.query(TankData.id)
                        query = query.filter(TankData.name == row.get('tank_name'))
                        try:
                            fk = query.first()[0]
                        except:
                            print(row)
                            print('It looks like we found a tank_name not in the tank_data table. Do you want to add it now?')
                            user_input = input('y/n: ')
                            if user_input == 'y':
                                try:
                                    tank_data = {'name': row.get('tank_name')}
                                    temp_session = self.get_session()
                                    query = temp_session.query(TankData).filter(TankData.name == tank_data['name'])
                                    existing_tank = query.first()
                                    
                                    if existing_tank is None:
                                        new_tank = TankData(**tank_data)
                                        temp_session.add(new_tank)
                                except:
                                    temp_session.rollback()
                                    print('something went wrong with temp_session tank update.')
                                finally:
                                    temp_session.commit()
                                    temp_session.close()

                        if fk:
                            # insert the chart information
                            row['tank_type_id'] = fk
                            new_chart_entry = TankCharts(**row)
                            session.add(new_chart_entry)
        
        except:
            session.rollback()
            print('Exception happened in tank_chart_entry method. Rolling things back...')

        finally:
            session.commit() # Commit all changes (inserts and updates) at once
            session.close()
        
    def tank_data_entry(self):
        '''
        This bad boy is specifically to enter in a set of tanks for tank_data when the db is 
        fresh. It is basically a db initialization script. It will use the tank name as the 
        unique identifier, although as this grows that will no longer work as the id. So, this
        takes tank names from the store data spreadsheet and makes an intial db entry based on
        those tanks. It will not insert this initial entry into the database if this tank name
        already exists.
        '''
        store_info_file = self.misc_dir / 'storeInfo_master.xlsx'

        if not store_info_file.exists():
            print(f"Error: Expected Excel file not found: {store_info_file}")
            print("Please ensure 'storeInfo_master.xlsx' exists in the specified directory.")
            return

        try:
            # Read the Excel file directly
            # Requires 'openpyxl' to be installed (pip install openpyxl)
            df = pd.read_excel(store_info_file)
        except Exception as e:
            print(f"Error reading Excel file {store_info_file.name}: {e}")
            print("Ensure 'openpyxl' is installed (pip install openpyxl) and the file is valid.")
            return
        
        # start by building a list of tank names from the store_info file
        tank_names = []
        fuel_types = ['regular', 'plus', 'premium', 'kerosene', 'diesel']
        
        try:
            session = self.get_session() # Get a new database session
            for fuel_type in fuel_types:
                for _, row in df.iterrows():
                    row_data = row.get(fuel_type)
                    if not pd.isna(row_data):
                        names = [
                            name.strip() for name
                            in str(row_data).split(',')
                        ]

                        for name in names:
                            if name not in tank_names:
                                tank_names.append(name)
            
            # build model attribute stuff for insertion using names
            for tank_name in tank_names:
                tank_data = {
                    'name': tank_name, # string
                    'manufacturer': None, # string
                    'model': None, # string
                    'capacity': None, # integer
                    'max_depth': None, # integer
                    'misc_info': None, # text
                    'chart_source': None, # text
                    'description': None # text
                }

                # build db upsertion
                query = session.query(TankData).filter(TankData.name == tank_data['name'])
                existing_tank = query.first()
                
                if existing_tank is None:
                    new_tank = TankData(**tank_data)
                    session.add(new_tank)

            session.commit() # Commit all changes (inserts and updates) at once
        finally:
            session.close()

    def store_tank_map(self):
        session = self.get_session()
        excel_file = self.misc_dir / 'storeInfo_master.xlsx'
        df = pd.read_excel(excel_file)

        try:
            # Iterate through each row of the DataFrame
            for _, row in df.iterrows():
                # Get identifying data from the row.
                fuel_types = ['regular', 'plus', 'premium', 'kerosene', 'diesel']
                tanks = {}

                store_num = row.get('store_num')
                riso_num = row.get('riso_num')

                if pd.isna(store_num):
                    store_num = None
                if pd.isna(riso_num):
                    riso_num = None

                for fuel_type in fuel_types:
                    fuel_tank_data = row.get(fuel_type)
                    if not pd.isna(fuel_tank_data):
                        tank_list = [
                            name.strip() for name
                            in str(fuel_tank_data).split(',')
                        ]

                        tanks[fuel_type] = tank_list
                
                query = session.query(StoreData.id)
                query = query.filter(
                    or_(
                        StoreData.store_num == store_num,
                        StoreData.riso_num == riso_num
                    )
                )
                store_data_row = query.first()
                
                for fuel_type in tanks:
                    for tank_name in tanks[fuel_type]:
                        query = session.query(TankData.id)
                        query = query.filter(TankData.name == tank_name)
                        tank_data_row = query.first()

                        store_tank_map_data = {
                            'store_id': store_data_row.id,
                            'tank_id': tank_data_row.id,
                            'fuel_type': fuel_type
                        }

                        new_mapping = StoreTankMap(**store_tank_map_data)

                        # add a quick check to see if the database holds all the tanks for this 
                        # store or not. This is a quck and dirty check, so don't expect too much
                        target_len = len(tanks[fuel_type])
                        query = session.query(StoreTankMap)
                        query = query.filter(StoreTankMap.store_id == store_data_row.id)
                        query = query.filter(StoreTankMap.fuel_type == fuel_type)
                        num_tanks_in_model = query.count()

                        if num_tanks_in_model < target_len:
                            session.add(new_mapping)

            session.commit()
                
        except Exception as e:
            session.rollback() # Rollback all changes if any error occurs during the process
            print(f"An error occurred during store data entry: {e}")

        finally:
            session.close()
