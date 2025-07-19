"""
This module provides the Analytics class, which is used to perform data analysis
on the speedGauge data. It includes methods for fetching data, calculating statistics,
and determining data filter values.
"""
import statistics
import json


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
        self.conn = self.models_util.get_db_connection()
        self.c = self.conn.cursor()

        # Fetch a list of all available dates from the database upon initialization.
        self.full_date_list = self.fetch_full_date_list()
        self.mssing_company_analytic_dates = self.fetch_missing_company_analytic_dates()

        # Determine the filter values for the data based on statistical analysis.
        self.data_filter_values = self.determine_data_filter_values()

    def close_connection(self):
        """Closes the database connection and cursor."""
        if self.c:
            self.c.close()
        if self.conn:
            self.conn.close()

    def standard_flow(self):
        self.company_standard_flow()
        self.driver_standard_flow()
        self.close_connection()

    def company_standard_flow(self):
        self.missing_analytics = self.fetch_missing_company_analytic_dates()

        for date, generated_records_allowed in self.missing_analytics:
            analytic_package = self.build_company_analytic_package(
                date, self.data_filter_values, generated_records_allowed
            )

            self.insert_company_analytics(
                analytic_package, date, generated_records_allowed
            )
        self.conn.commit()


    def driver_standard_flow(self):
        self.missing_driver_analytics = self.fetch_missing_driver_analytic_dates()
        total_records = len(self.missing_driver_analytics)
        print(f"Found {total_records} missing driver analytic records to process.")

        for i, (driver_id, date) in enumerate(self.missing_driver_analytics):
            analytic_package = self.build_driver_analytic_package(driver_id, date)
            self.insert_driver_analytics(analytic_package, driver_id, date)

            # Commit in batches of 1000
            if (i + 1) % 1000 == 0:
                self.conn.commit()
                print(f"Committed {i + 1}/{total_records} records...")

        # Commit any remaining records
        self.conn.commit()
        print(f"Finished committing all {total_records} records.")

    def insert_company_analytics(self, analytic_package, start_date, generated_records_allowed):
        """
        Inserts or updates company analytics data in the database.

        Args:
            analytic_package: A dictionary containing the analytics data.
            start_date: The start date of the analytics period.
            generated_records_allowed: A boolean indicating if generated records are allowed.
        """
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
            "speeding_trend_json": analytic_package.get("percent_speeding", {}).get("trend_json", None),

            "max_distance_driven": analytic_package.get("distance_driven", {}).get("max", None),
            "min_distance_driven": analytic_package.get("distance_driven", {}).get("min", None),
            "avg_distance_driven": analytic_package.get("distance_driven", {}).get("avg", None),
            "median_distance_driven": analytic_package.get("distance_driven", {}).get("median", None),
            "std_distance_driven": analytic_package.get("distance_driven", {}).get("stddev", None),
            "distance_trend_json": analytic_package.get("distance_driven", {}).get("trend_json", None),
        }

        # Construct the SQL query for ON DUPLICATE KEY UPDATE
        columns = ", ".join(data_to_insert.keys())
        placeholders = ", ".join(["%s"] * len(data_to_insert))
        update_statements = ", ".join([f"{col} = VALUES({col})" for col in data_to_insert if col not in ['start_date', 'generated_records_allowed']])

        query = f'''
        INSERT INTO company_analytics_table ({columns})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {update_statements}
        '''

        try:
            self.c.execute(query, list(data_to_insert.values()))
            print(f"Successfully inserted/updated analytics for {start_date} (generated_records_allowed={generated_records_allowed})")
        except Exception as e:
            self.conn.rollback()
            print(f"Error inserting/updating analytics for {start_date}: {e}")

    def fetch_full_date_list(self):
        """
        Fetches a list of all unique start_dates from the speedGauge_data table.

        Returns:
            A list of unique start_date strings, sorted in ascending order.
        """
        # Query to get a full list of available dates.
        query = """
        SELECT DISTINCT start_date
        FROM speedGauge_data
        ORDER BY start_date ASC
        """
        self.c.execute(query)
        rows = self.c.fetchall()

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
        # Get all existing combinations of start_date and generated_records_allowed
        query = """
        SELECT DISTINCT start_date, generated_records_allowed
        FROM company_analytics_table
        """
        self.c.execute(query)
        existing_analytics = {(row['start_date'], row['generated_records_allowed']) for row in self.c.fetchall()}

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
        self.c.execute(query)
        date_list = self.c.fetchall()
        return [date["start_date"] for date in date_list]

    def build_driver_analytic_package(self, driver_id, date):
        columns = ["percent_speeding", "distance_driven"]
        data_set = {}

        for column in columns:
            # Base query for statistics
            query_stats = f'''
            SELECT
                COUNT({column}) AS count,
                AVG({column}) AS avg,
                MAX({column}) AS max,
                MIN({column}) AS min,
                STDDEV({column}) AS stddev
            FROM speedGauge_data
            WHERE driver_id = %s
                AND start_date BETWEEN 
                    DATE_SUB(%s, INTERVAL 1 YEAR)
                    AND %s
            '''
            
            values = (driver_id, date, date )
            self.c.execute(query_stats, values)
            analytic_data = self.c.fetchone()
            
            query_points = f'''
            SELECT
                {column},
                start_date
            FROM speedGauge_data
            WHERE driver_id = %s
            AND start_date BETWEEN 
                DATE_SUB(
                    %s,
                    INTERVAL 1 YEAR
                    )
                AND %s
            ORDER BY start_date ASC
            '''
            self.c.execute(query_points, values)
            rows = self.c.fetchall()
            
            data_points = [
                (row['start_date'], row[column])
                for row in rows
                ]
            
            values_list = [
                value for _, value
                in data_points
                if value is not None
                ]
            
            try:
                median = statistics.median(values_list)
            except:
                median = None
            
            trend_data = {row['start_date'].isoformat(): str(row[column]) for row in rows}
                    
            analytic_data['median'] = median
            analytic_data['trend_json'] = json.dumps(trend_data)
            data_set[column] = analytic_data

        return data_set

    def build_company_analytic_package(
        self, date, filter_data, generated_records_allowed=False
    ):
        """
        Builds a dictionary of analytics for a given date.

        Args:
            date: The date for which to build the analytics.
            filter_data: A dictionary containing filter values for the data.

        Returns:
            A dictionary containing the calculated analytics for the specified date.
        """
        columns = ["percent_speeding", "distance_driven"]
        data_set = {}

        for column in columns:
            # Correctly access filter values from the flat dictionary
            filter_max = filter_data[f'{column}_max']
            filter_min = filter_data[f'{column}_min']

            # Base query for statistics
            query_stats = f'''
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
            '''
            
            filter_values = [date, filter_max, filter_min]

            # If generated records are not allowed, add the is_interpolated condition
            if not generated_records_allowed:
                query_stats += " AND is_interpolated = 0"

            self.c.execute(query_stats, filter_values)
            analytic_data = self.c.fetchone()

            # Second query to get all data points for median calculation
            query_points = f'''
            SELECT {column}
            FROM speedGauge_data
            WHERE start_date = %s
                AND {column} <= %s
                AND {column} >= %s
            '''
            
            # If generated records are not allowed, add the is_interpolated condition
            if not generated_records_allowed:
                query_points += " AND is_interpolated = 0"

            self.c.execute(query_points, filter_values)
            data_points_rows = self.c.fetchall()
            
            # Extract data points into a list
            data_points = [row[column] for row in data_points_rows]

            # Calculate the median if data exists
            if data_points:
                median = statistics.median(data_points)
                analytic_data["median"] = median
            else:
                analytic_data["median"] = None

            # Add trend data for the current column
            analytic_data['trend_json'] = self.fetch_trend_data(
                date, column, filter_max, filter_min
            )

            data_set[column] = analytic_data

        return data_set

    def fetch_trend_data(self, date, column, max_value, min_value):
        """
        Fetches speeding trend data for the year leading up to a specific date.

        Args:
            date: The end date for the trend analysis.
            max_spd: The maximum speeding percentage to include in the analysis.
            driver_id: (Optional) The ID of the driver to filter by.

        Returns:
            A dictionary with start_date as key and avg_percent_speeding as value.
        """
        query = f'''
        SELECT
            start_date,
            AVG({column}) AS avg_value
        FROM speedGauge_data
        WHERE start_date BETWEEN DATE_SUB(%s, INTERVAL 1 YEAR) AND %s
            AND {column} <= %s
            AND {column} >= %s
        GROUP BY start_date
        ORDER BY start_date ASC
        '''

        values = (date, date, max_value, min_value)

        self.c.execute(query, values)
        
        trend_data = {row['start_date'].isoformat(): str(row['avg_value']) for row in self.c.fetchall()}

        return json.dumps(trend_data)

    def determine_data_filter_values(self, stdev_threshold=1):
        '''
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
        '''
        
        columns = ["percent_speeding", "distance_driven"]
        data_set = {}

        for column in columns:
            query = f'''
            SELECT AVG({column}) AS avg,
                    STDDEV({column}) AS stddev
            FROM speedGauge_data
            WHERE is_interpolated = 0
            '''
            
            self.c.execute(query)
            result = self.c.fetchone()

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

        return data_set

    def fetch_missing_driver_analytic_dates(self):
        """
        Finds dates that are in the main speedGauge_data table but not in the
        driver_analytics_table for each driver.

        Returns:
            A list of tuples (driver_id, date) that are missing
            from the driver_analytics_table.
        """
        # Get all existing combinations of driver_id and start_date
        query = """
        SELECT DISTINCT sg.driver_id, sg.start_date
        FROM speedGauge_data sg
        LEFT JOIN driver_analytics_table da
            ON sg.driver_id = da.driver_id AND sg.start_date = da.start_date
        WHERE da.driver_id IS NULL
        """
        self.c.execute(query)
        missing_analytics = self.c.fetchall()
        
        return [(row['driver_id'], row['start_date']) for row in missing_analytics]

    def insert_driver_analytics(self, analytic_package, driver_id, start_date):
        """
        Inserts or updates driver analytics data in the database.

        Args:
            analytic_package: A dictionary containing the analytics data.
            driver_id: The ID of the driver.
            start_date: The start date of the analytics period.
        """
        ps_pkg = analytic_package.get("percent_speeding", {})
        dd_pkg = analytic_package.get("distance_driven", {})

        # Prepare the data for insertion
        data_to_insert = {
            "driver_id": driver_id,
            "start_date": start_date,
            "records_count": ps_pkg.get("count", 0),
            "avg_percent_speeding": ps_pkg.get("avg", None),
            "max_percent_speeding": ps_pkg.get("max", None),
            "min_percent_speeding": ps_pkg.get("min", None),
            "std_percent_speeding": ps_pkg.get("stddev", None),
            "median_percent_speeding": ps_pkg.get("median", None),
            "speeding_trend_json": ps_pkg.get("trend_json", None),
            "avg_distance_driven": dd_pkg.get("avg", None),
            "max_distance_driven": dd_pkg.get("max", None),
            "min_distance_driven": dd_pkg.get("min", None),
            "std_distance_driven": dd_pkg.get("stddev", None),
            "median_distance_driven": dd_pkg.get("median", None),
            "distance_trend_json": dd_pkg.get("trend_json", None),
        }

        # Construct the SQL query for ON DUPLICATE KEY UPDATE
        columns = ", ".join(data_to_insert.keys())
        placeholders = ", ".join(["%s"] * len(data_to_insert))
        update_statements = ", ".join([f"{col} = VALUES({col})" for col in data_to_insert if col not in ['driver_id', 'start_date']])

        query = f'''
        INSERT INTO driver_analytics_table ({columns})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {update_statements}
        '''

        try:
            self.c.execute(query, list(data_to_insert.values()))
        except Exception as e:
            self.conn.rollback()
            print(f"Error inserting/updating analytics for driver {driver_id} on {start_date}: {e}")