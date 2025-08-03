from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    creation_timestamp = Column(DateTime, server_default=func.now())
    first_name = Column(String(255))
    last_name = Column(String(255))
    driver_id = Column(Integer)  # Adjust this later if it becomes a ForeignKey

    def __repr__(self):
        return f"<Users(username='{self.username}', id={self.id})>"
