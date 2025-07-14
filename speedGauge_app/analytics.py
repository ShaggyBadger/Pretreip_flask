import statistics

class Analytics:
    def __init__(self, models_util):
        self.models_util = models_util
        
        self.full_date_list = self.fetch_full_date_list()
        
        self.data_filter_values = self.determine_data_filter_values()
    
    def fetch_full_date_list(self):
        conn = self.models_util.get_db_connection()
        c = conn.cursor()
        
        # get full list of available dates
        query = '''
        SELECT DISTINCT start_date
        FROM speedGauge_data
        ORDER BY start_date ASC
        '''
        c.execute(sql)
        rows = c.fetchl()
        conn.close()
        
        date_list = [
            row['start_date'] for row
            in rows
            ]
        
        return date_list
    
    fetch_missing_company_analytic_dates(self):
        conn = self.models_util.get_db_connection()
        c = conn.cursor()
        query = '''
        SELECT DISTINCT start_date
        FROM company_analytics_table
        '''
        c.execute(query)
        
        rows = c.fetchall()
        date_list = [
            row['start_date'] for row
            in rows
            ]
        
        filtered_date_list = []
        for date in self.full_date_list:
            if date not in date_list:
                filtered_date_list.append(date
        
        return filtered_date_list
        
    
    def get_date_list(self):
        conn = self.models_util.get_db_connection()
        c = conn.cursor()
        query = '''
        SELECT DISTINCT start_date
        FROM speedGauge_data
        WHERE start_date BETWEEN (
            SELECT DATE_SUB(MAX(start_date), INTERVAL 1 YEAR) FROM speedGauge_data
        ) AND (
            SELECT MAX(start_date) FROM speedGauge_data
        )
        ORDER BY start_date ASC;
        '''
        c.execute(query)
        date_list = c.fetchall()
        conn.close()
        return [date['start_date'] for date in date_list]
    
    def build_analytic_package(self, date, filter_data):
        conn = self.models_util.get_db_connection()
        c = conn.cursor()
        
        columns = [
            'percent_speeding',
            'distance_driven'
            ]
        data_set = {}
        
        for column in columns:
            filter_values = filter_data[column]
            filter_max = filter_values['max']
            filter_min = filter_values['min']
            query = f'''
            SELECT
                COUNT({column}) AS count,
                AVG({column}) AS avg,
                MAX({column}) AS max,
                MIN({column}) AS min,
                STDDEV({column}) AS stddev,
                {column} AS data_points
            FROM company_analytic_table
            WHERE start_date = %s
              AND {column} <= %s
              AND {column} >= %s
            '''
            values = (
                date,
                filter_max,
                filter_min
                )
            c.execute()
            analytic_data = c.fetchone()
            
            median = statistics.median(analytic_data['data_points'])
            
            analytic_data['median'] = median
            
            data_set[column] = analytic_data
        
        conn.close()
        return data_set
        
    def fetch_speeding_trend_dict(self, date, max_spd, driver_id=None):
        query = '''
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
        '''
        
        values = (date, max_spd)
        
        conn = self.models_util.get_db_connection()
        c = conn.cursor()
        c.execute(query, values)
        filtered_dates = c.fetchall()

    def determine_data_filter_values(self, stdev_threshold=1.5):
        """Determine the filter value for percent speeding based on average and standard deviation.
        
        We decided to use a threshold of 1.5 standard deviations above the mean to filter outliers.
        We also decided to use the entire dataset to calculate the average and standard deviation in
        order to ensure that we have a comprehensive view of the data.
        """
        columns = [
            'percent_speeding',
            'distance_driven'
            ]
        data_set = {}
        
        conn = self.models_util.get_db_connection()
        c = conn.cursor()
        
        for column in columns:
            query = '''
            SELECT AVG(%s) AS avg,
                   STDDEV(%s) AS stddev
            FROM speedGauge_data
            '''
            value = (column, column)
            c.execute(query, value)
            result = c.fetchone()
    
            filter_value = float(result['avg']) + float((stdev_threshold * result['stddev']))
            
            data_set[column] = round(filter_value, 2)
        
        conn.close()
        return data_set
