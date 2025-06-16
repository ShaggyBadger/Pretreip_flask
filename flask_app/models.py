import sqlite3
from flask_app import settings
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Utils:
	def __init__(self, debug_mode=False):
		self.user_exists = None
		self.debug_mode = debug_mode
	
	def db_connection(self, db_name=settings.db_name):
		conn = sqlite3.connect(db_name)
		return conn
	
	def register_user(self, username, password):
		conn = self.db_connection()
		c = conn.cursor()

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
			if self.debug_mode is True:
				print('User already exists in the database.')
			return None
		else:
			if self.debug_mode is True:
				print('registering user')
				print(f'Hashing password: {password}')
			hashed_password = generate_password_hash(str(password))
			if self.debug_mode is True:
				print(f'Hashed Password: {hashed_password}')
			
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
				
			
			# if username doesnt exist, go ahead and register user
			if self.debug_mode is True:
				print('Entering user into the database...')
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
			
			if self.debug_mode is True:
				print(f'User {username} has been entered into the database.\n')
			return user_id
	
	def check_password(self, username, password):
		conn = self.db_connection()
		c = conn.cursor()
		
		sql = '''
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

class CLI_Utils:
	def __init__(self, debug_mode=False):
		self.debug_mode = debug_mode
		self.users_json = settings.DATABASE_DIR / 'drivers.json'
	
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
	
	def enter_users_from_json(self):
		utils_obj = Utils(debug_mode=self.debug_mode)
		
		with open(self.users_json, 'r') as file:
			dict_list = json.load(file)

		for d in dict_list:
			# automatically register each driver in the list into database
			driver_id = d['driver_id']
			utils_obj.register_user(driver_id, driver_id)
		
		# now update user to have the driver_id as well. the registration process doesn't currently store
		# that information correctly. FIX THAT.
		conn = utils_obj.db_connection()
		c = conn.cursor()
		for d in dict_list:
			driver_id = d['driver_id']
			first_name = d['first_name']
			last_name = d['last_name']
			
			
			sql = '''
			UPDATE users
			SET
				first_name = ?,
				last_name = ?,
				driver_id = ?
			WHERE username = ?
			'''
			values = (first_name, last_name, driver_id, driver_id)
			c.execute(sql, values)
		conn.commit()
		conn.close()
