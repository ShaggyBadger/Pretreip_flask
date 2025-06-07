import sqlite3
import settings
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Utils():
	def __init__(self):
		self.user_exists = None
	
	def db_connection(self):
		db_name = settings.db_name
		conn = sqlite3.connect(db_name)
		return conn
	
	def register_user(self, username, password):
		hashed_password = generate_password_hash(str(password))
		
		conn = self.db_connection()
		c = conn.cursor()
		
		timestamp = datetime.now().isoformat()
		
		# check for existing user
		sql = '''
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
		sql = '''
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
		"""
		Verifies a user's password against the stored hash in the database.
		
		Args:
			username (str): The username of the account to check.
			
			password (str): The plain-text password to verify.
			
		Returns:
			tuple | None: Returns a tuple containing the user ID and hashed password if the credentials are valid, or None if authentication fails.
		
		Example:
			user = utils_obj.check_password("driver01", "mypassword123")
			
			if user:
				print("Login successful!")
			else:
				print("Invalid credentials.")
		"""
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
	
	def update_password(self, session, old_pass, new_pass):
		user_id = session['user_id']
		username = session['username']
		
		valid_password = self.check_password(username, old_pass)
		
		if valid_password:
			hashed_password = generate_password_hash(str(new_pass))
			
			conn = self.db_connection()
			c = conn.cursor()
			
			sql = '''
			UPDATE users
			SET password = ?
			WHERE id = ?
			'''
			values = (hashed_password, user_id)
			c.execute(sql, values)
			conn.commit()
			conn.close()
			return True
		else:
			return False
	
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
				TEXT
			)
		'''
		c.execute(sql)
		conn.commit()
		conn.close()

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
		utils_obj.build_db()
		self.clear_users()
		
		with open(json_file, 'r') as file:
			dict_list = json.load(file)

		for d in dict_list:
			driver_id = d['driver_id']
			first_name = d['first_name']
			last_name = d['last_name']
			
			user_id = utils_obj.register_user(driver_id, driver_id)
		
		conn = utils_obj.db_connection()
		c = conn.cursor()
		for d in dict_list:
			driver_id = d['driver_id']
			
			sql = f'''
			UPDATE users
			SET
				first_name = ?,
				last_name = ?
			WHERE username = ?
			'''
			values = (first_name, last_name, driver_id)
			
			c.execute(sql, values)
		conn.commit()
		conn.close()
			
			
def initialize_db():
	a = CLI_Utils()
	file_path = settings.DATABASE_DIR / 'drivers.json'
	a.enter_users_from_json(file_path)

if __name__ == '__main__':
	initialize_db()
