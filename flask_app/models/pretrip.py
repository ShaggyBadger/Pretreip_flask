from flask_app.extensions import db
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from datetime import datetime, timezone

class Equipment(db.Model):
    __tablename__ = 'equipment'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)            # e.g., "Tractor", "Trailer", "Forklift"
    equipment_type = Column(String(255), nullable=False)  # e.g., "tractor", "trailer", "other"
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class PretripItem(db.Model):
    __tablename__ = 'pretrip_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(Integer, db.ForeignKey('equipment.id'), nullable=False)
    name = Column(String(255), nullable=False)           # e.g., "Oil Level", "Fire Extinguisher", "Paperwork"
    notes = Column(Text)                                 # optional guidance or instructions
    date_field_required = Column(Integer, default=0)     # 0 = False, 1 = True
    numeric_field_required = Column(Integer, default=0)  # e.g., odometer reading
    boolean_field_required = Column(Integer, default=0)  # e.g., yes/no checkboxes
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class PretripRecord(db.Model):
    __tablename__ = 'pretrip_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(Integer, db.ForeignKey('equipment.id'), nullable=False)
    driver_id = Column(Integer, nullable=False) # FK to users table
    pretrip_date = Column(DateTime, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Example JSON/Text field for storing all item values if needed
    item_values_json = Column(Text) # e.g., {"Oil Level": "Full", "Paperwork Expiration": "2025-09-10"}
