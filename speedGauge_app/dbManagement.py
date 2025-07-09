import pymysql
import pandas as pd
from flask_app import settings, models
from datetime import datetime


class DbManagement:
    def __init__(self):
        self.models_utils = models.Utils()

    def get_dates(self):
        """
        Returns a list full of  start_date in ASC order. oldest date is first, newest date is index[-1]

        the date is str from db, it can be used for query and also turned into datetime object later
        """
        conn = self.models_utils.get_db_connection()
        c = conn.cursor()

        sql = """
    SELECT DISTINCT start_date
    FROM speedGauge_data
    ORDER BY start_date ASC
    """
        c.execute(sql)
        datelist = [date["start_date"] for date in c.fetchall()]
        c.fetchall()
        conn.close()

        return datelist

    def get_all_driver_id(self):
        conn = self.models_utils.get_db_connection()
        c = conn.cursor()

        sql = """
    SELECT DISTINCT driver_id
    FROM speedGauge_data
    """
        c.execute(sql)
        id_list = [id["driver_id"] for id in c.fetchall()]

        conn.close()
        return id_list

    def gen_interpolated_speeds(self):
        """
        This will go through entire database and look for missing percent_speedings then generate
        some interpolated values to fill in the gap
        """
        datelist = self.get_dates()
        id_list = self.get_all_driver_id()

        conn = self.models_utils.get_db_connection()
        c = conn.cursor()

        sql = """
    SELECT
      driver_id,
      start_date,
      percent_speeding
    FROM speedGauge_data
    """
        c.execute(sql)
        all_rows = c.fetchall()
        conn.close()

        main_dict = {}

        for row in all_rows:
            if row["driver_id"] in main_dict:
                sub_dict = main_dict[row["driver_id"]]
                sub_dict[row["start_date"]] = row["percent_speeding"]
            else:
                main_dict[row["driver_id"]] = {
                    row["start_date"]: row["percent_speeding"]
                }

        for driver in main_dict:
            d_dict = main_dict[driver]
            for date in datelist:
                if date not in d_dict:
                    d_dict[date] = None

        test_dict = main_dict[1201619]
        for date in datelist:
            print(date, test_dict[date])
