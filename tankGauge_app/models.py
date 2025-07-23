from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from flask_app.db import Base  # or wherever your Base is declared


class TankData(Base):
    __tablename__ = 'tank_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)
    manufacturer = Column(String)
    model = Column(String)
    capacity = Column(Integer)
    max_depth = Column(Integer)
    misc_info = Column(Text)
    chart_source = Column(Text)

    # Relationship to tank charts
    tank_charts = relationship("TankCharts", back_populates="tank_type")

    def __repr__(self):
        return f"<TankData(name={self.name}, capacity={self.capacity})>"
        
class StoreInfo(Base):
    __tablename__ = 'store_info'

    id = Column(Integer, primary_key=True, autoincrement=True)
    store_num = Column(Integer, unique=True)
    riso_num = Column(Integer)
    store_name = Column(String)
    store_type = Column(String)
    num_tanks = Column(Integer)
    regular = Column(String)
    premium = Column(String)
    plus = Column(String)
    kerosene = Column(String)
    diesel = Column(String)
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

    # Backref to TankData
    tank_type = relationship("TankData", back_populates="tank_charts")

    def __repr__(self):
        return f"<TankCharts(tank_name={self.tank_name}, inches={self.inches}, gallons={self.gallons})>"


