import os
from datetime import datetime
import json
import pymysql # For MySQL connection
import pymysql.cursors # To get results as dictionaries from MySQL
from flask_app import settings
from werkzeug.security import generate_password_hash, check_password_hash
from flask_app.settings import BASE_DIR, speedGuage_data_tbl_name

# --- MySQL Database Configuration (Read from Environment Variables) ---
# These variables MUST be set in your Linode's environment (e.g., ~/.bashrc)
MYSQL_HOST = os.environ.get('MYSQL_HOST')
MYSQL_USER = os.environ.get('MYSQL_USER')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
MYSQL_DB = os.environ.get('MYSQL_DB')

class Utils:
	'''General utilities to use with the database'''
	def __init__(self, debug_mode=False):
		self.user_exists = None
		self.debug_mode = debug_mode
	
	def get_db_connection(self):
		"""
    Establishes and returns a MySQL database connection.
    Reads connection details from environment variables.
    """
    # Ensure all necessary MySQL environment variables are set
		if not all([MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB]):
			raise ValueError(
        "MySQL environment variables (MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB) "
        "must be set for the application to connect to the database."
      )
		
		try:
      # print("Attempting to connect to MySQL...") # Uncomment for debugging
			conn = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor # Returns rows as dictionaries
      )
      # print("Successfully connected to MySQL.") # Uncomment for debugging
			return conn
		except pymysql.Error as e:
			print(f"ERROR: Could not connect to MySQL database: {e}")
			raise ConnectionError("Failed to connect to MySQL database.") from e
	
	def register_user(self, username, password):
		'''Automated way to register users from a json file'''
		conn = self.get_db_connection()
		c = conn.cursor()

		# check for existing user
		sql = '''
		SELECT id
		FROM users
		WHERE username = %s
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
				
			# if username doesnt exist, go ahead and register user
			if self.debug_mode is True:
				print('Entering user into the database...')
			sql = '''
			INSERT INTO users(
				username,
				password
				)
			VALUES (
				%s,
				%s
				)
			'''
			
			values = (
				username,
				hashed_password
				)
			c.execute(sql, values)
			user_id = c.lastrowid
			conn.commit()
			conn.close()
			
			if self.debug_mode is True:
				print(f'User {username} has been entered into the database.\n')
			return user_id

	def check_password(self, username, password):
		'''This checks the password and hash and all that from the database'''
		conn = self.get_db_connection()
		c = conn.cursor()
		
		sql = '''
		SELECT id, password
		FROM users
		WHERE username = %s
		'''
		value = (username,)
		c.execute(sql, value)
		user = c.fetchone()
		
		conn.close()
		
		if user and check_password_hash(
			user['password'],
			password
			):
			return user
			
		else:
			return None

	def build_db(self):
		'''Used to automate creating the database'''
		conn = self.get_db_connection()
		c = conn.cursor()
		
		# create table
		sql = '''
		CREATE TABLE IF NOT EXISTS users (
			id INT AUTO_INCREMENT PRIMARY KEY,
			username VARCHAR(80) UNIQUE NOT NULL,
			password VARCHAR(255) NOT NULL,
			creation_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
			first_name VARCHAR(255),
			last_name VARCHAR(255),
			driver_id INT
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
		'''
		
		c.execute(sql)
		conn.commit()
		conn.close()

	def retrieve_driver_id(self, user_id):
		'''Takes in the user id from session and finds driver_id'''
		conn = self.get_db_connection()
		c = conn.cursor()
		
		sql = '''
		SELECT driver_id
		FROM users
		WHERE id = %s
		'''
		value = (user_id,)
		c.execute(sql, value)
		result = c.fetchone()
		conn.close()
		
		if result:
			return result['driver_id']
		else:
			return None

class CLI_Utils:
	def __init__(self, debug_mode=False):
		self.debug_mode = debug_mode
		self.users_json = settings.DATABASE_DIR / 'drivers.json'
	
	def clear_users(self):
		'''Clear all users and reset AUTOINCREMENT counter.'''
		utils_obj = Utils()
		conn = utils_obj.get_db_connection()
		c = conn.cursor()
		c.execute('DELETE FROM users')
		c.execute('ALTER TABLE users AUTO_INCREMENT = 1')
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
		conn = utils_obj.get_db_connection()
		c = conn.cursor()
		for d in dict_list:
			driver_id = d['driver_id']
			first_name = d['first_name']
			last_name = d['last_name']
			
			
			sql = '''
			UPDATE users
			SET
				first_name = %s,
				last_name = %s,
				driver_id = %s
			WHERE username = %s
			'''
			values = (first_name, last_name, driver_id, driver_id)
			c.execute(sql, values)
		conn.commit()
		conn.close()
