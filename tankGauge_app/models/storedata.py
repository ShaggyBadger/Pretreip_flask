from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from dbConnector import Base  # or wherever your Base is declared

class StoreData(Base):
    __tablename__ = 'store_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    store_num = Column(Integer, unique=True)
    riso_num = Column(Integer, unique=True)
    store_name = Column(String(255)) # ws1, greensboro 3, etc.
    store_type = Column(String(255)) # exxon, 7-11, speedway, etc
    address = Column(String(255))
    city = Column(String(255))
    state = Column(String(255))
    zip = Column(Integer)
    county = Column(String(255))
    lat = Column(Float)
    lon = Column(Float)
    install_date = Column(Date)  # Could use Date if data is normalized
    overfill_protection = Column(String(255))

    # Relationship to StoreTankMap: One StoreData can have many tanks mapped to it
    # via the StoreTankMap association table.
    # 'store_tanks_map' on StoreData will be a list of StoreTankMap objects
    store_tanks_map = relationship("StoreTankMap", back_populates="store_info")

    def __repr__(self):
        return f"<StoreData(store_num={self.store_num}, city={self.city})>"
