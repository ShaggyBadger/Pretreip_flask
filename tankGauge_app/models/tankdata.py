from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from dbConnector import Base  # or wherever your Base is declared

class TankData(Base):
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
