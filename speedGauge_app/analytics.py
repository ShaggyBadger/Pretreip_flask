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
        for date in self.mssing_company_analytic_dates:
            # Build the analytic package for each missing date.
            analytic_package = self.build_analytic_package(date, self.data_filter_values)
            # Here you would typically save the analytic_package to the database or perform further processing.
            # For now, we just print it.
            print(f"Analytics for {date}")
            p = analytic_package['percent_speeding']
            d = analytic_package['distance_driven']
            print("Percent Speeding Analytics:")
            for key, value in p.items():
                print(f"{key}: {value}")
            print("\nDistance Driven Analytics:")
            for key, value in d.items():
                print(f"{key}: {value}")
            input('Press Enter to continue.../n************/n')

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
        company_analytics_table.

        Returns:
            A list of date strings that are missing from the company_analytics_table.
        """
        conn = self.models_util.get_db_connection()
        c = conn.cursor()
        query = """
        SELECT DISTINCT start_date
        FROM company_analytics_table
        """
        c.execute(query)

        rows = c.fetchall()
        conn.close()
        
        # Extract the date strings from the query results.
        date_list = [row["start_date"] for row in rows]

        # Filter the full date list to find dates not present in the analytics table.
        filtered_date_list = []
        for date in self.full_date_list:
            if date not in date_list:
                filtered_date_list.append(date)

        return filtered_date_list

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