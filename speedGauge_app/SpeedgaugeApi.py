from datetime import datetime, timedelta


class Api:
    """
    this is the main way to get the data for a user. should return dicts and stuff
    """

    def __init__(self, driver_id, models_utils):
        self.driver_id = driver_id
        self.models_utils = models_utils

    def build_speedgauge_report(self):
        """
        returns a dict:
          key: start_date
          value: speedgauge rows (dicts) for that date
        """

        conn = self.models_utils.get_db_connection()
        c = conn.cursor()

        sql = """
    SELECT DISTINCT *
    FROM speedGauge_data
    WHERE driver_id = %s
    ORDER BY start_date DESC;
    """
        value = (self.driver_id,)
        c.execute(sql, value)
        row_dicts = c.fetchall()
        conn.close()

        # Clean the row dicts if needed, make url short etc etc
        cleaned_row_dicts = [self.clean_dict(row) for row in row_dicts]

        return cleaned_row_dicts

    def clean_dict(self, row_dict):
        keys_to_remove = ["raw_json", "is_interpolated", "id"]

        for i in keys_to_remove:
            if i in row_dict:
                del row_dict[i]

        if "url" in row_dict and len(row_dict["url"]) > 10:
            url = row_dict["url"]
            row_dict["url"] = (
                f'<a href="{url}" target="_blank" rel="noopener noreferrer">Click for map</a>'
            )

        return row_dict

    def get_speedGauge_row(self, start_date):
        """
        this takes in the start_date and returns the row of data in dict form from the db
        """
        conn = self.models_utils.get_db_connection()
        c = conn.cursor()

        sql = """
    SELECT *
    FROM speedGauge_data
    WHERE driver_id = %s AND
    start_date = %s;
    """
        values = (self.driver_id, start_date)

        c.execute(sql, values)

        row_dict = c.fetchone()

        conn.close()

        return row_dict

    def get_dates(self, cuttoff_time=365):
        """
        default cuttoff time is a year, although you can override if you want. just do it with num days

        Returns a list full of  start_date in ASC order. oldest date is first, newest date is index[-1]

        the date is str from db, it can be used for query and also turned into datetime object later
        """
        cuttoff_date = datetime.now() - timedelta(days=cuttoff_time)

        conn = self.models_utils.get_db_connection()
        c = conn.cursor()

        sql = """
    SELECT DISTINCT start_date
    FROM speedGauge_data
    ORDER BY start_date ASC
    """
        c.execute(sql)
        datelist = c.fetchall()
        conn.close()

        filtered_list = []

        for date in datelist:
            start_date = date["start_date"]

            if start_date is not None and start_date >= cuttoff_date:
                filtered_list.append(start_date.isoformat())

        return filtered_list

    def extract_data(self, info):
        """
        takes in a dictionary of data from a row in the db and creates a new dict of info for the template to use in making the webpage
        """
        extracted_data = {
            "fname": info["first_name"],
            "lname": info["last_name"],
            "driver_id": info["driver_id"],
        }

        return extracted_data

    def get_driver_analytics(self, driver_id, start_date):
        """
        Returns the driver analytic package for a given driver_id and start_date.
        """
        conn = self.models_utils.get_db_connection()
        c = conn.cursor()

        sql = """
            SELECT *
            FROM driver_analytics_table
            WHERE driver_id = %s AND start_date = %s;
            """
        values = (driver_id, start_date)
        c.execute(sql, values)
        analytic_data = c.fetchone()
        conn.close()

        return analytic_data

    def get_company_analytics(self, start_date, generated_records_allowed=True):
        """
        Returns the company analytic package for a given start_date and generated_records_allowed status.
        """
        conn = self.models_utils.get_db_connection()
        c = conn.cursor()

        sql = """
            SELECT *
            FROM company_analytics_table
            WHERE start_date = %s AND generated_records_allowed = %s;
            """
        values = (start_date, generated_records_allowed)
        c.execute(sql, values)
        analytic_data = c.fetchone()
        conn.close()

        return analytic_data
