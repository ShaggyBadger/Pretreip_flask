import math

class CompanyAnalytics:
    def __init__(self):
        self.data = []
        print('analytics initialized')
    
    def get_date_list(self):
        pass
    
    def build_analysis_package(self, date, max_spd):
        query = '''
        SELECT start_date, AVG(percent_speeding)
        FROM speedGauge_data
        WHERE start_date BETWEEN DATE_SUB(%s, INTERVAL 1 YEAR) AND %s
            AND percent_speeding <= %s
        GROUP BY start_date
        ORDER BY start_date ASC
        '''
    
    

    
