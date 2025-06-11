from rich.traceback import install
install()
from flask_app import speedGauge, models

#processor = speedGauge.Processor()
#processor.create_table_from_json()

class Initialize:
  def __init__(self):
    pass

  def initialize_db(self):
    print('Initializing the database...')
    models_util = models.Utils(debug_mode=True)
    print(models_util.debug_mode)
    models_cli_util = models.CLI_Utils()
    speedGauge_processor = speedGauge.Processor()

    print('Building the Database....')
    models_util.build_db()
    print('\nEntering users from json file....')
    models_cli_util.enter_users_from_json()
    print('\nCreating speedGauge table....')
    speedGauge_processor.create_table_from_json()
    
if __name__ == '__main__':
  initializer = Initialize()
  initializer.initialize_db()