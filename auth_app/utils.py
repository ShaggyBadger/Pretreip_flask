from werkzeug.security import generate_password_hash, check_password_hash
from flask import session as flask_session
from flask_app.extensions import db
from flask_app.models.users import Users # Import the Users model
from sqlalchemy import text, text as sa_text # Import text for raw SQL

class Utils:
    def __init__(self):
        pass


    def register_user(
            self,
            username,
            password,
            first_name=None,
            last_name=None,
            driver_id=None,
            admin_level=0,
            dot_number=None,
            role='standard'
            ):
        # Check if user already exists
        user = Users.query.filter_by(username=username).first()

        if user:
            self.user_exists = True
            return None # let routes know this user already exists in the db
        
        else:
            hashed_password = generate_password_hash(str(password))

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

            try:
                db.session.add(new_user)
                db.session.commit()
            except Exception as e:
                print("Commit failed:", e)
                db.session.rollback()

            return new_user
    
    def check_password(self, identifier, password):
        user = None
        # Try to find user by username (email)
        user = Users.query.filter_by(username=identifier).first()

        if user and check_password_hash(user.password, password):
            return user # Return the whole user object
        else:
            return None
