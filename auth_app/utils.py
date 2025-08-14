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
        input(user)
        if user:
            self.user_exists = True
            return None # let routes know this user already exists in the db
        
        else:
            hashed_password = generate_password_hash(str(password))
            print(password)
            input(hashed_password)

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
            print(db.engine.url)

            input(new_user)
            try:
                db.session.add(new_user)
                db.session.commit()
            except Exception as e:
                print("Commit failed:", e)
                db.session.rollback()

            user_check = Users.query.get(new_user.id)
            print(f"Queried user after commit: {user_check}")
            input('commited to db')

            return new_user.id
    
    def check_password(self, identifier, password):
        # Try to find user by username (which is now email)
        query = Users.query
        query = query.filter(Users.username == str(identifier))
        q = query.first()
        result = Users.query.filter_by(username=identifier).first()
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
                    dot_number=result.dot_number,
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
                        dot_number=result.dot_number,
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
