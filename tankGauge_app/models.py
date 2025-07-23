from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from dbConnector import Base  # or wherever your Base is declared


class TankData(Base):
    __tablename__ = 'tank_data'

    id = Column(Integer, primary_key=True, autoincrement=True) # the identifier
    name = Column(String) # general name. 15k119 etc
    manufacturer = Column(String) # sometimes we have this if have proper charts
    model = Column(String) # sometimes we have this if we have proper charts
    capacity = Column(Integer) # maximum gallons
    max_depth = Column(Integer) # maximum inches
    misc_info = Column(Text) # stuff whatever in there
    chart_source = Column(Text) # pdf, spreadsheet, whatever
    description = Column(Text) # description is put out in website

    # Relationship to tank charts - associate chart rows with these tanks
    tank_charts = relationship("TankCharts", back_populates="tank_type")

    def __repr__(self):
        return f"<TankData(name={self.name}, capacity={self.capacity})>"
        
class StoreData(Base):
    __tablename__ = 'store_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    store_num = Column(Integer, unique=True)
    riso_num = Column(Integer, unique=True)
    store_name = Column(String) # ws1, greensboro 3, etc.
    store_type = Column(String) # exxon, 7-11, speedway, etc
    address = Column(String)
    city = Column(String)
    state = Column(String)
    zip = Column(Integer)
    county = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    install_date = Column(String)  # Could use Date if data is normalized
    overfill_protection = Column(String)

    def __repr__(self):
        return f"<StoreInfo(store_num={self.store_num}, city={self.city})>"
        
class TankCharts(Base):
    __tablename__ = 'tank_charts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tank_type_id = Column(Integer, ForeignKey('tank_data.id'), nullable=False)
    inches = Column(Integer, nullable=False)
    gallons = Column(Integer, nullable=False)
    tank_name = Column(String, nullable=False)
    misc_info = Column(Text)

    # Backref to TankData
    tank_type = relationship("TankData", back_populates="tank_charts")

    def __repr__(self):
        return f"<TankCharts(tank_name={self.tank_name}, inches={self.inches}, gallons={self.gallons})>"

class StoreTankMap(Base):
    __tablename__ = 'store_tank_map'

    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey('store_data.id'), nullable=False)
    tank_id = Column(Integer, ForeignKey('tank_data.id'), nullable=False)
    fuel_type = Column(String(10))

    # Backref to TankData and StoreData
    store = relationship('StoreInfo', back_populates="")