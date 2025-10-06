from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from flask_app.extensions import db

class Users(db.Model):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'pretrip_db'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    # store only password hashes (use passlib or werkzeug.security)
    # from werkzeug.security import generate_password_hash, check_password_hash
    # user.password = generate_password_hash(plain_password)
    password = Column(String(255), nullable=False)
    creation_timestamp = Column(DateTime, server_default=func.now())
    first_name = Column(String(255))
    last_name = Column(String(255))
    driver_id = Column(String(255))
    admin_level = Column(Integer, nullable=False, server_default='0')
    dot_number = db.Column(String(255))
    role = db.Column(String(50), nullable=False, server_default='standard')

    # FIX: Use string for class name to prevent circular import
    inspections = relationship('PretripInspection', back_populates='user', cascade='all, delete-orphan')
    templates = relationship('PretripTemplate', back_populates='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Users(username='{self.username}', id={self.id})>"