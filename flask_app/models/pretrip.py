from flask_app.extensions import db
from sqlalchemy import (
    Column, Integer, String, Date, Boolean, Text, DateTime, ForeignKey, func,
    UniqueConstraint, Enum, JSON
)
from sqlalchemy.orm import relationship

class Equipment(db.Model):
    __tablename__ = 'equipment'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    equipment_type = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    default_template_id = Column(Integer, ForeignKey('pretrip_templates.id', ondelete='SET NULL'), nullable=True)
    default_template = relationship('PretripTemplate', back_populates='default_for_equipments')

    inspections = relationship('PretripInspection', back_populates='equipment', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Equipment(name='{self.name}', id={self.id})>"

class Blueprint(db.Model):
    __tablename__ = 'pretrip_blueprints'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    equipment_type = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    items = relationship('BlueprintItem', back_populates='blueprint', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Blueprint(name='{self.name}', id={self.id})>"

class BlueprintItem(db.Model):
    __tablename__ = 'pretrip_blueprint_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    blueprint_id = Column(Integer, ForeignKey('pretrip_blueprints.id', ondelete='CASCADE'), nullable=False)

    section = Column(String(255))
    name = Column(String(255), nullable=False)
    details = Column(Text)
    notes = Column(Text)

    date_field_required = Column(Boolean, default=False)
    numeric_field_required = Column(Boolean, default=False)
    boolean_field_required = Column(Boolean, default=False)
    text_field_required = Column(Boolean, default=False)

    blueprint = relationship('Blueprint', back_populates='items')

    def __repr__(self):
        return f"<BlueprintItem(name='{self.name}', blueprint_id={self.blueprint_id})>"

class PretripItem(db.Model):
    __tablename__ = 'pretrip_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(Integer, ForeignKey('equipment.id'), nullable=True)

    section = Column(String(255))
    name = Column(String(255), nullable=False)
    details = Column(Text)
    notes = Column(Text)

    date_field_required = Column(Boolean, default=False)
    numeric_field_required = Column(Boolean, default=False)
    boolean_field_required = Column(Boolean, default=False)
    text_field_required = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    results = relationship('PretripResult', back_populates='item')

    def __repr__(self):
        return f"<PretripItem(name='{self.name}', id={self.id})>"

class PretripTemplate(db.Model):
    __tablename__ = 'pretrip_templates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    equipment_type = Column(String(255), nullable=True)
    user_id = Column(Integer, ForeignKey('pretrip_db.users.id'), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship('Users', back_populates='templates')
    items = relationship('TemplateItem', back_populates='template', cascade='all, delete-orphan')
    default_for_equipments = relationship('Equipment', back_populates='default_template')
    inspections = relationship('PretripInspection', back_populates='template')

    def __repr__(self):
        return f"<PretripTemplate(name='{self.name}', id={self.id})>"

class TemplateItem(db.Model):
    __tablename__ = 'template_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey('pretrip_templates.id', ondelete='CASCADE'), nullable=False)

    section = Column(String(255))
    name = Column(String(255), nullable=False)
    details = Column(Text)
    notes = Column(Text)
    display_order = Column(Integer, default=0)

    date_field_required = Column(Boolean, default=False)
    numeric_field_required = Column(Boolean, default=False)
    boolean_field_required = Column(Boolean, default=False)
    text_field_required = Column(Boolean, default=False)

    template = relationship('PretripTemplate', back_populates='items')

    def __repr__(self):
        return f"<TemplateItem(name='{self.name}', template_id={self.template_id})>"

class PretripInspection(db.Model):
    __tablename__ = 'pretrip_inspections'

    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(Integer, ForeignKey('equipment.id', ondelete='RESTRICT'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('pretrip_db.users.id', ondelete='RESTRICT'), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey('pretrip_templates.id', ondelete='SET NULL'), nullable=True)

    inspection_datetime = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    results = relationship('PretripResult', back_populates='inspection', cascade='all, delete-orphan')
    equipment = relationship('Equipment', back_populates='inspections')
    user = relationship('Users', back_populates='inspections')
    template = relationship('PretripTemplate', back_populates='inspections')

    def __repr__(self):
        return f"<PretripInspection(id={self.id}, equipment_id={self.equipment_id}, user_id={self.user_id})>"

class PretripResult(db.Model):
    __tablename__ = 'pretrip_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    inspection_id = Column(Integer, ForeignKey('pretrip_inspections.id', ondelete='CASCADE'), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey('template_items.id', ondelete='RESTRICT'), nullable=False, index=True)

    item_snapshot = Column(JSON, nullable=False)  # {"name": "...", "numeric_field_required": True, ...}

    boolean_value = Column(Boolean, nullable=True)
    numeric_value = Column(String(50), nullable=True)
    date_value = Column(Date, nullable=True)
    text_value = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    severity = Column(Enum('ok', 'defect', 'action_required', name='result_severity'), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    inspection = relationship('PretripInspection', back_populates='results')
    item = relationship('PretripItem', back_populates='results')
    photos = relationship('PretripPhoto', back_populates='result', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<PretripResult(inspection_id={self.inspection_id}, item_id={self.item_id})>"

class PretripPhoto(db.Model):
    __tablename__ = 'pretrip_photos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    result_id = Column(Integer, ForeignKey('pretrip_results.id', ondelete='CASCADE'), nullable=False)
    file_path = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    description = Column(Text, nullable=True)

    result = relationship('PretripResult', back_populates='photos')

    def __repr__(self):
        return f"<PretripPhoto(id={self.id}, result_id={self.result_id})>{f.result_id})>"