from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from dbConnector import Base  # or wherever your Base is declared

class TankCharts(Base):
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
