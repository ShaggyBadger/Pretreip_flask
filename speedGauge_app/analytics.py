import math

class Analytics:
    def __init__(self, models_util):
        self.models_util = models_util
        date_list = self.get_date_list()
        percent_speeding_filter_value = self.determine_percent_speeding_filter()
        print(percent_speeding_filter_value)
    
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
        
    def build_analysis_package(self, date, max_spd, driver_id=None):
        query = '''
        SELECT start_date, AVG(percent_speeding)
        FROM speedGauge_data
        WHERE start_date BETWEEN DATE_SUB(%s, INTERVAL 1 YEAR) AND %s
            AND percent_speeding <= %s
        GROUP BY start_date
        ORDER BY start_date ASC
        '''

    def determine_percent_speeding_filter(self, stdev_threshold=1.5):
        """Determine the filter value for percent speeding based on average and standard deviation.
        
        We decided to use a threshold of 1.5 standard deviations above the mean to filter outliers.
        We also decided to use the entire dataset to calculate the average and standard deviation in
        order to ensure that we have a comprehensive view of the data.
        """
        conn = self.models_util.get_db_connection()
        c = conn.cursor()
        query = '''
        SELECT AVG(percent_speeding) AS avg,
               STDDEV(percent_speeding) AS stddev
        FROM speedGauge_data
        '''
        c.execute(query)
        result = c.fetchone()
        conn.close()

        filter_value = float(result['avg']) + float((stdev_threshold * result['stddev']))
        return round(filter_value, 2)