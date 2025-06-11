from rich.traceback import install
from rich import print
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
    models_cli_util = models.CLI_Utils(debug_mode=True)
    speedGauge_processor = speedGauge.Processor()

    print('Building the Database....')
    models_util.build_db()
    print('\nEntering users from json file....')
    models_cli_util.enter_users_from_json()
    print('\nCreating speedGauge table....')
    speedGauge_processor.create_table_from_json()
    
if __name__ == '__main__':
  d = {
    'a': 123,
    'name': 'Josh',
    'debug': True,
    'score': [95, 32,44,62]
  }
  print(d)