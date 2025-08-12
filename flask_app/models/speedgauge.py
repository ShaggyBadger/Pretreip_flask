from flask_app.extensions import db
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, DECIMAL

class SpeedGaugeData(db.Model):
    __tablename__ = 'speedGauge_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_name = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    driver_id = Column(Integer)
    vehicle_type = Column(String(255))
    percent_speeding = Column(DECIMAL(5,2))
    is_interpolated = Column(Integer) # tinyint(1)
    max_speed_non_interstate_freeway = Column(DECIMAL(6,2))
    percent_speeding_non_interstate_freeway = Column(DECIMAL(5,2))
    worst_incident_date = Column(DateTime)
    incident_location = Column(Text)
    speed_limit = Column(Integer)
    speed = Column(Integer)
    speed_cap = Column(String(255))
    custom_speed_restriction = Column(String(255))
    distance_driven = Column(Integer)
    url = Column(String(2048))
    url_lat = Column(DECIMAL(10,8))
    url_lon = Column(DECIMAL(11,8))
    location = Column(String(255))
    percent_speeding_numerator = Column(DECIMAL(10,2))
    percent_speeding_denominator = Column(DECIMAL(10,2))
    max_speed_interstate_freeway = Column(DECIMAL(6,2))
    percent_speeding_interstate_freeway = Column(DECIMAL(5,2))
    incidents_interstate_freeway = Column(Integer)
    observations_interstate_freeway = Column(Integer)
    incidents_non_interstate_freeway = Column(Integer)
    observations_non_interstate_freeway = Column(Integer)
    difference = Column(Integer)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    raw_json = Column(Text)

class CompanyAnalytics(db.Model):
    __tablename__ = 'company_analytics_table'

    id = Column(Integer, primary_key=True, autoincrement=True)
    start_date = Column(DateTime, nullable=False)
    generated_records_allowed = Column(Integer) # INT (Boolian value: 1, 0)
    records_count = Column(Integer, nullable=False)
    std_filter_value = Column(Float)
    max_percent_speeding = Column(Float)
    min_percent_speeding = Column(Float)
    avg_percent_speeding = Column(Float)
    median_percent_speeding = Column(Float)
    std_percent_speeding = Column(Float)
    percent_change_percent_speeding = Column(Float)
    abs_change_percent_speeding = Column(Float)
    max_distance_driven = Column(Float)
    min_distance_driven = Column(Float)
    avg_distance_driven = Column(Float)
    median_distance_driven = Column(Float)
    std_distance_driven = Column(Float)
    percent_change_distance_driven = Column(Float)
    abs_change_distance_driven = Column(Float)
    speeding_trend_json = Column(Text) # JSON
    distance_trend_json = Column(Text) # JSON

class DriverAnalytics(db.Model):
    __tablename__ = 'driver_analytics_table'

    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_id = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    std_filter_threshold = Column(Float)
    current_week_percent_speeding = Column(Float, nullable=False)
    previous_week_percent_speeding = Column(Float)
    percent_change_percent_speeding = Column(Float)
    abs_change_percent_speeding = Column(Float)
    max_percent_speeding = Column(Float)
    min_percent_speeding = Column(Float)
    avg_percent_speeding = Column(Float)
    median_percent_speeding = Column(Float)
    std_percent_speeding = Column(Float)
    current_week_distance_driven = Column(Float, nullable=False)
    previous_week_distance_driven = Column(Float)
    percent_change_distance_driven = Column(Float)
    abs_change_distance_driven = Column(Float)
    max_distance_driven = Column(Float)
    min_distance_driven = Column(Float)
    avg_distance_driven = Column(Float)
    median_distance_driven = Column(Float)
    std_distance_driven = Column(Float)
    records_count = Column(Integer)
    speeding_trend_json = Column(Text) # JSON
    distance_trend_json = Column(Text) # JSON
