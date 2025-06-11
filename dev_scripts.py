from flask_app import speedGauge, settings
import json

processor = speedGauge.Processor()
processor.create_table_from_json()
