from pathlib import Path
from rich.traceback import install
import pandas as pd
from dbConnector import fetch_session
from .models import StoreData
install()

class Processing:
    def __init__(self):
        # establish paths to the excel files we want to insert into database
        self.tankGauge_files = Path('tankGauge_app/tankGauge_files')
        self.charts_dir = self.tankGauge_files / 'tank_charts'
        self.misc_dir = self.tankGauge_files / 'misc'

        # convert all xlsx files to csv format
        self.convert_all_to_csv()
    
    def convert_all_to_csv(self):        
        # List of directories to search for Excel files
        directories_to_scan = [self.misc_dir, self.charts_dir]
        
        converted_count = 0
        skipped_count = 0

        for current_dir in directories_to_scan:
            print(f"\nScanning directory for xlsx to csv conversions: {current_dir}")
            # Use .rglob('*.xlsx') to find all .xlsx files recursively within the directory
            for excel_file_path in current_dir.rglob('*.xlsx'):
                print(f"  Attempting to convert: {excel_file_path.name}")
                
                csv_file_path = excel_file_path.with_suffix('.csv')
                
                try:
                    # Read the Excel file
                    df = pd.read_excel(excel_file_path)
                    
                    # Write to CSV
                    df.to_csv(csv_file_path, index=False)
                    excel_file_path.unlink()
                    print(f"    Successfully converted to: {csv_file_path.name}")
                    converted_count += 1
                except FileNotFoundError:
                    print(f"    Error: File not found at {excel_file_path}. Skipping.")
                    skipped_count += 1
                except Exception as e:
                    print(f"    Could not convert {excel_file_path.name} to CSV format. Reason: {e}")
                    skipped_count += 1

    def store_data_entry(self):
        file = self.misc_dir / 'storeInfo_master.csv'
        df = pd.read_csv(file)

        session = next(fetch_session())
        try:
            stores_to_add = []
            for index, row in df.iterrows():
                current_store_num = row.get('store_num')
                print(current_store_num)
                stores_to_add.append(StoreData(
                    store_num=row['store_num'],
                    riso_num=row['riso_num'],
                    store_name=row['store_name'],
                    store_type=row['store_type'],
                    address=row['address'],
                    city=row['city'],
                    state=row['state'],
                    zip_code=row['zip_code'],
                    latitude=row['latitude'],
                    longitude=row['longitude'],
                    install_date=row['install_date'],
                    overfill_protection=row['overfill_protection']
                ))

            if stores_to_add:
                #session.bulk_save_objects(stores_to_add)
                #session.commit()
                print(f"Successfully inserted {len(stores_to_add)} new store records.")
            else:
                print("No new stores to add.")

        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")
        finally:
            session.close()

    def tank_chart_entry(self):
        pass

    def tank_data_entry(self):
        pass

    def store_tank_map(self):
        pass
