from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from flask_app.extensions import db

class StoreData(db.Model):
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

class StoreTankMap(db.Model):
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

class TankCharts(db.Model):
    __tablename__ = 'tank_charts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tank_type_id = Column(Integer, ForeignKey('tank_data.id'), nullable=False)
    inches = Column(Integer, nullable=False)
    gallons = Column(Integer, nullable=False)
    tank_name = Column(String(255), nullable=False)
    misc_info = Column(Text)

    # Relationship back to TankData: Each TankCharts row belongs to one TankData type.
    # 'tank_type' on TankCharts will be a single TankData object.
    tank_type = relationship("TankData", back_populates="tank_charts")

    def __repr__(self):
        return f"<TankCharts(tank_name={self.tank_name}, inches={self.inches}, gallons={self.gallons}, tank_type_id={self.tank_type_id})>"

class TankData(db.Model):
    __tablename__ = 'tank_data'

    id = Column(Integer, primary_key=True, autoincrement=True) # the identifier
    name = Column(String(255)) # general name. 15k119 etc
    manufacturer = Column(String(255)) # sometimes we have this if have proper charts
    model = Column(String(255)) # sometimes we have this if we have proper charts
    capacity = Column(Integer) # maximum gallons
    max_depth = Column(Integer) # maximum inches
    misc_info = Column(Text) # stuff whatever in there
    chart_source = Column(Text) # pdf, spreadsheet, whatever
    description = Column(Text) # description is put out in website

    # Relationship to TankCharts: One TankData type can have many TankCharts rows
    # 'tank_charts' on TankData will be a list of TankCharts objects
    tank_charts = relationship("TankCharts", back_populates="tank_type")

    # Relationship to StoreTankMap: A TankData type can be mapped to many stores
    # via the StoreTankMap association table.
    # 'mapped_stores' on TankData will be a list of StoreTankMap objects
    mapped_stores = relationship("StoreTankMap", back_populates="tank_info")

    def __repr__(self):
        return f"<TankData(name={self.name}, capacity={self.capacity})>"
