import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_app.extensions import db
from flask_app.models.users import Users # Import the Users model
from sqlalchemy import text, text as sa_text # Import text for raw SQL


class Utils:
    """General utilities to use with the database"""

    def __init__(self, debug_mode=False):
        self.user_exists = None
        self.debug_mode = debug_mode

    def register_user(self, username, password, first_name=None, last_name=None, driver_id=None, admin_level=0, dot_number=None, role='standard'):
        # Check if user already exists
        user = Users.query.filter_by(username=username).first()
        if user:
            self.user_exists = True
            if self.debug_mode:
                print("User already exists in the database.")
            return None
        else:
            if self.debug_mode:
                print("registering user")
                print(f"Hashing password: {password}")
            hashed_password = generate_password_hash(str(password))
            if self.debug_mode:
                print(f"Hashed Password: {hashed_password}")

            new_user = Users(
                username=username,
                password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                driver_id=driver_id,
                admin_level=admin_level,
                dot_number=dot_number,
                role=role
            )
            db.session.add(new_user)
            db.session.commit()

            if self.debug_mode:
                print(f"User {username} has been entered into the database.\n")
            return new_user.id

    def check_password(self, identifier, password):
        # Try to find user by username (which is now email)
        input(f'Identifier: {identifier} | Type: {type(identifier)}')
        query = Users.query
        query = query.filter(Users.username == str(identifier))
        q = query.first()
        input(f'josh queru: {q}')
        result = Users.query.filter_by(username=identifier).first()
        input('made result')
        input(result)
        try:
            # Try to find user by username (which is now email) using raw SQL with schema
            result = db.session.execute(
                text("SELECT * FROM pretrip_db.users WHERE username = :identifier LIMIT 1"), # ADD SCHEMA
                {"identifier": identifier}
            ).fetchone()

            if result:
                user = Users(
                    id=result.id,
                    username=result.username,
                    password=result.password,
                    creation_timestamp=result.creation_timestamp,
                    first_name=result.first_name,
                    last_name=result.last_name,
                    driver_id=result.driver_id,
                    admin_level=result.admin_level,
                    role=result.role
                )
            print(f"DEBUG: User found by username (raw SQL with schema): {user}")

            # If not found by username, try to find by driver_id using raw SQL with schema
            if not user: # Only try driver_id if username lookup failed
                result = db.session.execute(
                    text("SELECT * FROM pretrip_db.users WHERE driver_id = :identifier LIMIT 1"), # ADD SCHEMA
                    {"identifier": identifier}
                ).fetchone()

                if result:
                    user = Users(
                        id=result.id,
                        username=result.username,
                        password=result.password,
                        creation_timestamp=result.creation_timestamp,
                        first_name=result.first_name,
                        last_name=result.last_name,
                        driver_id=result.driver_id,
                        admin_level=result.admin_level,
                        role=result.role
                    )
                print(f"DEBUG: User found by driver_id (raw SQL with schema): {user}")

        except Exception as e:
            print(f"DEBUG: Error finding user (raw SQL with schema): {e}")
            user = None # Ensure user is None if an exception occurs and no user was found
            pass

        if user and check_password_hash(user.password, password):
            return user # Return the whole user object
        else:
            return None

    def retrieve_driver_id(self, user_id):
        user = Users.query.get(user_id)
        if user:
            return user.driver_id
        else:
            return None


class CLI_Utils:
    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode
        # Assuming settings.DATABASE_DIR is still valid for finding drivers.json
        from flask_app import settings # Import settings here to avoid circular import
        self.users_json = settings.DATABASE_DIR / "drivers.json"

    def clear_users(self):
        db.session.query(Users).delete()
        db.session.execute(sa_text("ALTER TABLE users AUTO_INCREMENT = 1"))
        db.session.commit()
        print("Table *user* has been reset")

    def enter_users_from_json(self):
        utils_obj = Utils(debug_mode=self.debug_mode)

        with open(self.users_json, "r") as file:
            dict_list = json.load(file)

        for d in dict_list:
            driver_id = d["driver_id"]
            utils_obj.register_user(
                username=str(driver_id),
                password=str(driver_id),
                first_name=d.get("first_name"),
                last_name=d.get("last_name"),
                driver_id=driver_id,
                dot_number=943113,
                role='premium'
            )

