from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from dbConnector import Base  # or wherever your Base is declared

class StoreTankMap(Base):
    __tablename__ = 'store_tank_map'

    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey('store_data.id'), nullable=False)
    tank_id = Column(Integer, ForeignKey('tank_data.id'), nullable=False)
    fuel_type = Column(String(10))

    # Relationship back to StoreData: Each StoreTankMap entry links to one StoreData.
    # 'store_info' on StoreTankMap will be a single StoreData object.
    store_info = relationship('StoreData', back_populates='store_tanks_map')

    # Relationship back to TankData: Each StoreTankMap entry links to one TankData type.
    # 'tank_info' on StoreTankMap will be a single TankData object.
    tank_info = relationship('TankData', back_populates='mapped_stores')

    def __repr__(self):
        return f"<StoreTankMap(store_id={self.store_id}, tank_id={self.tank_id}, fuel_type={self.fuel_type})>"
