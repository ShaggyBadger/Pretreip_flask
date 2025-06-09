from speedGauge import db_management

class Controller():
	def __init__(self, config=None):
		self.config = config
	
	def process_new_speedGauge(self, file):
		pass
	
	def test_package(self):
		a = db_management.test()
		

