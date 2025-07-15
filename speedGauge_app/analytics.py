"""
This module provides the Analytics class, which is used to perform data analysis
on the speedGauge data. It includes methods for fetching data, calculating statistics,
and determining data filter values.
"""
import statistics


class Analytics:
    """
    A class to perform analytics on speedGauge data.
    """

    def __init__(self, models_util):
        """
        Initializes the Analytics object.

        Args:
            models_util: An object that provides database connection utilities.
        """
        self.models_util = models_util

        # Fetch a list of all available dates from the database upon initialization.
        self.full_date_list = self.fetch_full_date_list()
        self.mssing_company_analytic_dates = self.fetch_missing_company_analytic_dates()

        # Determine the filter values for the data based on statistical analysis.
        self.data_filter_values = self.determine_data_filter_values()
    
    def standard_flow(self):
        self.company_standard_flow()
        self.driver_standard_flow()

    def company_standard_flow(self):
        self.missing_analytics = self.fetch_missing_company_analytic_dates()

        for date, generated_records_allowed in self.missing_analytics:
            if generated_records_allowed:
                # Don't filter, use wide values
                filter_data = {
                    'percent_speeding_max': 999999, 'percent_speeding_min': 0,
                    'distance_driven_max': 999999, 'distance_driven_min': 0
                }
            else:
                # Use pre-calculated filters
                filter_data = self.data_filter_values

            analytic_package = self.build_analytic_package(date, filter_data)
            self.insert_company_analytics(analytic_package, date, generated_records_allowed)

    def driver_standard_flow(self):
        self.missing_driver_analytics = self.fetch_missing_driver_analytic_dates()

        for driver_id, date in self.missing_driver_analytics:
            analytic_package = self.build_driver_analytic_package(driver_id, date, self.data_filter_values)
            self.insert_driver_analytics(analytic_package, driver_id, date)

    def insert_company_analytics(self, analytic_package, start_date, generated_records_allowed):
        """
        Inserts or updates company analytics data in the database.

        Args:
            analytic_package: A dictionary containing the analytics data.
            start_date: The start date of the analytics period.
            generated_records_allowed: A boolean indicating if generated records are allowed.
        """
        conn = self.models_util.get_db_connection()
        c = conn.cursor()

        # Prepare the data for insertion
        data_to_insert = {
            "start_date": start_date,
            "generated_records_allowed": generated_records_allowed,
            "records_count": analytic_package.get("percent_speeding", {}).get("count", 0),
            "std_filter_value": self.data_filter_values.get("stdev_threshold", None),
            "max_percent_speeding": analytic_package.get("percent_speeding", {}).get("max", None),
            "min_percent_speeding": analytic_package.get("percent_speeding", {}).get("min", None),
            "avg_percent_speeding": analytic_package.get("percent_speeding", {}).get("avg", None),
            "median_percent_speeding": analytic_package.get("percent_speeding", {}).get("median", None),
            "std_percent_speeding": analytic_package.get("percent_speeding", {}).get("stddev", None),
            "max_distance_driven": analytic_package.get("distance_driven", {}).get("max", None),
            "min_distance_driven": analytic_package.get("distance_driven", {}).get("min", None),
            "avg_distance_driven": analytic_package.get("distance_driven", {}).get("avg", None),
            "median_distance_driven": analytic_package.get("distance_driven", {}).get("median", None),
            "std_distance_driven": analytic_package.get("distance_driven", {}).get("stddev", None),
        }

        # Construct the SQL query for ON DUPLICATE KEY UPDATE
        columns = ", ".join(data_to_insert.keys())
        placeholders = ", ".join(["%s"] * len(data_to_insert))
        update_statements = ", ".join([f"{col} = VALUES({col})" for col in data_to_insert if col not in ['start_date', 'generated_records_allowed']])

        query = f"""
        INSERT INTO company_analytics_table ({columns})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {update_statements}
        """

        try:
            c.execute(query, list(data_to_insert.values()))
            conn.commit()
            print(f"Successfully inserted/updated analytics for {start_date} (generated_records_allowed={generated_records_allowed})")
        except Exception as e:
            conn.rollback()
            print(f"Error inserting/updating analytics for {start_date}: {e}")
        finally:
            conn.close()

    def fetch_full_date_list(self):
        """
        Fetches a list of all unique start_dates from the speedGauge_data table.

        Returns:
            A list of unique start_date strings, sorted in ascending order.
        """
        conn = self.models_util.get_db_connection()
        c = conn.cursor()

        # Query to get a full list of available dates.
        query = """
        SELECT DISTINCT start_date
        FROM speedGauge_data
        ORDER BY start_date ASC
        """
        c.execute(query)
        rows = c.fetchall()
        conn.close()

        # Extract the date strings from the query results.
        date_list = [row["start_date"] for row in rows]

        return date_list

    def fetch_missing_company_analytic_dates(self):
        """
        Finds dates that are in the main speedGauge_data table but not in the
        company_analytics_table for each value of generated_records_allowed.

        Returns:
            A list of tuples (date, generated_records_allowed) that are missing
            from the company_analytics_table.
        """
        conn = self.models_util.get_db_connection()
        c = conn.cursor()

        # Get all existing combinations of start_date and generated_records_allowed
        query = """
        SELECT DISTINCT start_date, generated_records_allowed
        FROM company_analytics_table
        """
        c.execute(query)
        existing_analytics = {(row['start_date'], row['generated_records_allowed']) for row in c.fetchall()}
        conn.close()

        # Determine the full set of required analytics
        required_analytics = set()
        for date in self.full_date_list:
            required_analytics.add((date, True))
            required_analytics.add((date, False))

        # Find the missing analytics
        missing_analytics = list(required_analytics - existing_analytics)

        return missing_analytics

    def get_date_list(self):
        """
        Gets a list of unique start_dates from the last year in the speedGauge_data table.

        Returns:
            A list of date strings from the last year, sorted in ascending order.
        """
        conn = self.models_util.get_db_connection()
        c = conn.cursor()
        query = """
        SELECT DISTINCT start_date
        FROM speedGauge_data
        WHERE start_date BETWEEN (
            SELECT DATE_SUB(MAX(start_date), INTERVAL 1 YEAR) FROM speedGauge_data
        ) AND (
            SELECT MAX(start_date) FROM speedGauge_data
        )
        ORDER BY start_date ASC;
        """
        c.execute(query)
        date_list = c.fetchall()
        conn.close()
        return [date["start_date"] for date in date_list]

    def build_analytic_package(self, date, filter_data):
        """
        Builds a dictionary of analytics for a given date.

        Args:
            date: The date for which to build the analytics.
            filter_data: A dictionary containing filter values for the data.

        Returns:
            A dictionary containing the calculated analytics for the specified date.
        """
        conn = self.models_util.get_db_connection()
        c = conn.cursor()

        columns = ["percent_speeding", "distance_driven"]
        data_set = {}

        for column in columns:
            # Correctly access filter values from the flat dictionary
            filter_max = filter_data[f'{column}_max']
            filter_min = filter_data[f'{column}_min']

            # First query for aggregate statistics
            query_stats = f"""
            SELECT
                COUNT({column}) AS count,
                AVG({column}) AS avg,
                MAX({column}) AS max,
                MIN({column}) AS min,
                STDDEV({column}) AS stddev
            FROM speedGauge_data
            WHERE start_date = %s
                AND {column} <= %s
                AND {column} >= %s
            """
            values = (date, filter_max, filter_min)
            c.execute(query_stats, values)
            analytic_data = c.fetchone()

            # Second query to get all data points for median calculation
            query_points = f"""
            SELECT {column}
            FROM speedGauge_data
            WHERE start_date = %s
                AND {column} <= %s
                AND {column} >= %s
            """
            c.execute(query_points, values)
            data_points_rows = c.fetchall()
            
            # Extract data points into a list
            data_points = [row[column] for row in data_points_rows]

            # Calculate the median if data exists
            if data_points:
                median = statistics.median(data_points)
                analytic_data["median"] = median
            else:
                analytic_data["median"] = None

            data_set[column] = analytic_data

        conn.close()
        return data_set

    def fetch_speeding_trend_dict(self, date, max_spd, driver_id=None):
        """
        Fetches speeding trend data for the year leading up to a specific date.

        Args:
            date: The end date for the trend analysis.
            max_spd: The maximum speeding percentage to include in the analysis.
            driver_id: (Optional) The ID of the driver to filter by.

        Returns:
            None. The fetched data is not currently used or returned.
        """
        query = """
        SELECT
            start_date,
            AVG(percent_speeding),
            MAX(percent_speeding),
            MIN(percent_speeding),
            STDDEV(percent_speeding)
        FROM speedGauge_data
        WHERE start_date BETWEEN DATE_SUB(%s, INTERVAL 1 YEAR) AND %s
            AND percent_speeding <= %s
        GROUP BY start_date
        ORDER BY start_date ASC
        """

        values = (date, max_spd)

        conn = self.models_util.get_db_connection()
        c = conn.cursor()
        c.execute(query, values)
        # The fetched data is not currently used or returned.
        filtered_dates = c.fetchall()

    def determine_data_filter_values(self, stdev_threshold=1):
        """
        Determines the filter values for data columns based on mean and standard deviation.

        This method calculates a max and min filter value for specified columns. The max is
        the mean plus a number of standard deviations, and the min is the mean minus the
        same. This is used to filter out outlier data points.

        Args:
            stdev_threshold (int, optional): The number of standard deviations to use
                                             for the filter threshold. Defaults to 1.

        Returns:
            dict: A dictionary containing the calculated max and min filter values
                  for each column.
        """
        columns = ["percent_speeding", "distance_driven"]
        data_set = {}

        conn = self.models_util.get_db_connection()
        c = conn.cursor()

        for column in columns:
            query = f"""
            SELECT AVG({column}) AS avg,
                    STDDEV({column}) AS stddev
            FROM speedGauge_data
            """
            c.execute(query)
            result = c.fetchone()

            # Calculate max and min filter values based on the standard deviation threshold.
            max_filter_value = float(result["avg"]) + float(
                (stdev_threshold * result["stddev"])
            )
            min_filter_value = float(result["avg"]) - float(
                (stdev_threshold * result["stddev"])
            )

            data_set[f'{column}_max'] = round(max_filter_value, 2)
            # For percent_speeding, the minimum cannot be less than 0.
            if column == "percent_speeding":
                data_set[f'{column}_min'] = 0
            else:
                data_set[f'{column}_min'] = round(min_filter_value, 2)

        conn.close()
        return data_set

    def fetch_missing_driver_analytic_dates(self):
        """
        Finds dates that are in the main speedGauge_data table but not in the
        driver_analytics_table for each driver.

        Returns:
            A list of tuples (driver_id, date) that are missing
            from the driver_analytics_table.
        """
        conn = self.models_util.get_db_connection()
        c = conn.cursor()

        # Get all existing combinations of driver_id and start_date
        query = """
        SELECT DISTINCT driver_id, start_date
        FROM driver_analytics_table
        """
        c.execute(query)
        existing_analytics = {(row['driver_id'], row['start_date']) for row in c.fetchall()}
        conn.close()

        # Determine the full set of required analytics
        required_analytics = set()
        driver_list = self.get_driver_list()
        for driver_id in driver_list:
            for date in self.full_date_list:
                required_analytics.add((driver_id, date))

        # Find the missing analytics
        missing_analytics = list(required_analytics - existing_analytics)

        return missing_analytics

    def insert_driver_analytics(self, analytic_package, driver_id, start_date):
        """
        Inserts or updates driver analytics data in the database.

        Args:
            analytic_package: A dictionary containing the analytics data.
            driver_id: The ID of the driver.
            start_date: The start date of the analytics period.
        """
        conn = self.models_util.get_db_connection()
        c = conn.cursor()

        # Prepare the data for insertion
        data_to_insert = {
            "driver_id": driver_id,
            "start_date": start_date,
            "records_count": analytic_package.get("percent_speeding", {}).get("count", 0),
            "std_filter_value": self.data_filter_values.get("stdev_threshold", None),
            "current_week_percent_speeding": analytic_package.get("percent_speeding", {}).get("avg", None),
            "current_week_distance_driven": analytic_package.get("distance_driven", {}).get("avg", None),
        }

        # Construct the SQL query for ON DUPLICATE KEY UPDATE
        columns = ", ".join(data_to_insert.keys())
        placeholders = ", ".join(["%s"] * len(data_to_insert))
        update_statements = ", ".join([f"{col} = VALUES({col})" for col in data_to_insert if col not in ['driver_id', 'start_date']])

        query = f"""
        INSERT INTO driver_analytics_table ({columns})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {update_statements}
        """

        try:
            c.execute(query, list(data_to_insert.values()))
            conn.commit()
            print(f"Successfully inserted/updated analytics for driver {driver_id} on {start_date}")
        except Exception as e:
            conn.rollback()
            print(f"Error inserting/updating analytics for driver {driver_id} on {start_date}: {e}")
        finally:
            conn.close()