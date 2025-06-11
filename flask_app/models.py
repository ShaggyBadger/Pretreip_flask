import sqlite3
from flask_app import settings
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Utils():
	def __init__(self):
		self.user_exists = None
	
	def db_connection(self, db_name=settings.db_name):
		conn = sqlite3.connect(db_name)
		return conn
	
	def register_user(self, username, password):
		hashed_password = generate_password_hash(str(password))
		
		conn = self.db_connection()
		c = conn.cursor()
		
		timestamp = datetime.now().isoformat()
		
		# check for existing user
		sql = f'''
		SELECT id
		FROM users
		WHERE username = ?
		'''
		value = (username,)
		c.execute(sql, value)
		user = c.fetchone()
		if user:
			self.user_exists = True
			return None
		
		# if username doesnt exist, go ahead and register user
		sql = f'''
		INSERT INTO users(
			username,
			password,
			creation_timestamp
			)
		VALUES (
			?,
			?,
			?
			)
		'''
		
		values = (
			username,
			hashed_password,
			timestamp
			)
		c.execute(sql, values)
		user_id = c.lastrowid
		conn.commit()
		conn.close()
		
		return user_id
	
	def check_password(self, username, password):
		conn = self.db_connection()
		c = conn.cursor()
		
		sql = f'''
		SELECT id, password
		FROM users
		WHERE username = ?
		'''
		value = (username,)
		c.execute(sql, value)
		user = c.fetchone()
		
		conn.close()
		
		if user and check_password_hash(
			user[1],
			password
			):
			return user
			
		else:
			return None
	
	def build_db(self):
		conn = self.db_connection()
		c = conn.cursor()
		
		# create table
		sql = '''
		CREATE TABLE IF NOT EXISTS users(
			id
			  INTEGER
			  PRIMARY KEY
			  AUTOINCREMENT,
			username
			  TEXT
			  UNIQUE
			  NOT NULL,
			password
			  TEXT
			  NOT NULL,
			creation_timestamp
			  TEXT,
			first_name
				TEXT,
			last_name
				TEXT,
			driver_id
			  INTEGER
			)
		'''
		c.execute(sql)
		conn.commit()
		conn.close()
	
	def retrieve_driver_id(self, user_id):
		conn = self.db_connection()
		c = conn.cursor()
		
		sql = '''
		SELECT driver_id
		FROM users
		WHERE id = ?
		'''
		value = (user_id,)
		c.execute(sql, value)
		result = c.fetchone()
		conn.close()
		
		if result:
			return result[0]
		else:
			return None

class CLI_Utils():
	def __init__(self):
		pass
	
	def clear_users(self):
		'''Clear all users and reset AUTOINCREMENT counter.'''
		utils_obj = Utils()
		conn = utils_obj.db_connection()
		c = conn.cursor()
		c.execute('DELETE FROM users')
		c.execute('DELETE FROM sqlite_sequence WHERE name="users"')
		conn.commit()
		conn.close()
		print('Table *user* has been reset')
	
	def enter_users_from_json(self, json_file):
		utils_obj = Utils()
		
		with open(json_file, 'r') as file:
			dict_list = json.load(file)

		for d in dict_list:
			driver_id = d['driver_id']
			
			user_id = utils_obj.register_user(driver_id, driver_id)
		
		conn = utils_obj.db_connection()
		c = conn.cursor()
		for d in dict_list:
			driver_id = d['driver_id']
			first_name = d['first_name']
			last_name = d['last_name']
			
			
			sql = f'''
			UPDATE users
			SET
				first_name = ?,
				last_name = ?,
				driver_id = ?
			WHERE username = ?
			'''
			values = (first_name, last_name, driver_id, driver_id)
			print(sql, values)
			
			c.execute(sql, values)
		conn.commit()
		conn.close()
			
			
		

if __name__ == '__main__':
	from pathlib import Path
	BASE_DIR = Path(__file__).resolve().parent

	# Main directories inside root
	DATA_DIR = BASE_DIR / 'data'
	DATABASE_DIR = DATA_DIR / 'database'
	
	db_name = DATABASE_DIR / 'site_database.db'
	a = CLI_Utils()
	b = Utils()
	
	b.build_db(db_name=db_name)
	a.clear_users()
	file_path = DATABASE_DIR / 'drivers.json'
	a.enter_users_from_json(file_path)
