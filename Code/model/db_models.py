from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, CHAR, Integer, JSON, DateTime, Boolean, Float

Base = declarative_base()

class DB_Location(Base):
    __tablename__ = "location"
    id = Column(String(100), primary_key=True)
    name = Column(String(100), nullable=False)
    timezone = Column(String(50), nullable=False)
    
class DB_Airport(Base):
    __tablename__ = "airport"
    id = Column(CHAR(3), primary_key=True)
    name = Column(String(100), nullable=False)
    location_id = Column(String(100), nullable=False)
    
class DB_Direct_Flight(Base):
    __tablename__ = "direct_flight"
    id = Column(Integer, primary_key=True, autoincrement=True)
    origin_airport_code = Column(CHAR(3), nullable=False)
    destination_airport_code = Column(CHAR(3), nullable=False)
    total_duration_minute = Column(Integer, nullable=False)
    duration_list = Column(JSON, nullable=False)
    total_transfer_minute = Column(Integer, nullable=False)
    transfer_duration_list = Column(JSON, nullable=False)
    stop_count = Column(Integer, nullable=False)
    stop_list = Column(JSON, nullable=False)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)
    carrier_count = Column(Integer, nullable=False)
    carrier_list = Column(JSON, nullable=False)
    flight_number_list = Column(JSON, nullable=False)
    agent = Column(String(50), nullable=False)
    agent_rating = Column(Float, nullable=False)
    price = Column(Integer, nullable=False)
    self_transfer = Column(Boolean, nullable=False)
    from_carrier = Column(Boolean, nullable=False)
    get_time_utc = Column(DateTime(timezone=True), nullable=False)
    
class DB_Round_Flight(Base):
    __tablename__ = "round_flight"

    id = Column(Integer, primary_key=True, autoincrement=True)
    origin_airport_code = Column(CHAR(3), nullable=False)
    destination_airport_code = Column(CHAR(3), nullable=False)
    
    # Incoming flight details
    in_total_duration_minute = Column(Integer, nullable=False)
    in_duration_list = Column(JSON, nullable=False)
    in_total_transfer_minute = Column(Integer, nullable=False)
    in_transfer_duration_list = Column(JSON, nullable=False)
    in_stop_count = Column(Integer, nullable=False)
    in_stop_list = Column(JSON, nullable=False)
    in_departure_time = Column(DateTime, nullable=False)
    in_arrival_time = Column(DateTime, nullable=False)
    in_carrier_count = Column(Integer, nullable=False)
    in_carrier_list = Column(JSON, nullable=False)
    in_flight_number_list = Column(JSON, nullable=False)

    # Outgoing flight details
    out_total_duration_minute = Column(Integer, nullable=False)
    out_duration_list = Column(JSON, nullable=False)
    out_total_transfer_minute = Column(Integer, nullable=False)
    out_transfer_duration_list = Column(JSON, nullable=False)
    out_stop_count = Column(Integer, nullable=False)
    out_stop_list = Column(JSON, nullable=False)
    out_departure_time = Column(DateTime, nullable=False)
    out_arrival_time = Column(DateTime, nullable=False)
    out_carrier_count = Column(Integer, nullable=False)
    out_carrier_list = Column(JSON, nullable=False)
    out_flight_number_list = Column(JSON, nullable=False)

    # Booking & metadata
    agent = Column(String(50), nullable=False)
    agent_rating = Column(Float, nullable=False)
    price = Column(Integer, nullable=False)
    self_transfer = Column(Boolean, nullable=False)
    from_carrier = Column(Boolean, nullable=False)
    get_time_utc = Column(DateTime(timezone=True), nullable=False)