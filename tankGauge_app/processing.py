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
    
    def store_data_entry(self):
        file = self.misc_dir / 'storeInfo_master.xlsx'
        df = pd.read_excel(file)
        print(df.columns)

    def tank_chart_entry(self):
        pass

    def tank_data_entry(self):
        pass

    def store_tank_map(self):
        pass
