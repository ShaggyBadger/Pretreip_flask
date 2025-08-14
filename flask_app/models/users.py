from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from flask_app.extensions import db

class Users(db.Model):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'pretrip_db'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    creation_timestamp = Column(DateTime, server_default=func.now())
    first_name = Column(String(255))
    last_name = Column(String(255))
    driver_id = Column(String(255))
    admin_level = Column(Integer, nullable=False, server_default='0')
    dot_number = db.Column(String(255))
    role = db.Column(String(50), nullable=False, server_default='standard')

    def __repr__(self):
        return f"<Users(username='{self.username}', id={self.id})>"
