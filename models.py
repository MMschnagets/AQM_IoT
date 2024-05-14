from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Create engine and session
engine = create_engine('sqlite:///air_quality_monitoring.db', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()


# Define tables
class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    measurements = relationship("Measurement", back_populates="location")


class Parameter(Base):
    __tablename__ = 'parameters'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    unit = Column(String)
    measurements = relationship("Measurement", back_populates="parameter")


class Measurement(Base):
    __tablename__ = 'measurements'

    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey('locations.id'))
    parameter_id = Column(Integer, ForeignKey('parameters.id'))
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    location = relationship("Location", back_populates="measurements")
    parameter = relationship("Parameter", back_populates="measurements")


# Define AQI Result Table
class AQIResult(Base):
    __tablename__ = 'aqi_results'

    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey('locations.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    aqi_value = Column(Integer)


# Define AQI results for each pollutant
class AQIPollutantResult(Base):
    __tablename__ = 'aqi_pollutant_results'

    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey('locations.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    pollutant_name = Column(String)
    aqi_value = Column(Integer)

    # Define relationship to Location table
    location = relationship("Location", back_populates="aqi_pollutant_results")


# Add a back reference in Location class
Location.aqi_pollutant_results = relationship("AQIPollutantResult", back_populates="location")

# Create tables
Base.metadata.create_all(engine)

# Define breakpoints and corresponding AQI ranges for each pollutant
breakpoints = {
    "O3_8hr": [(0.0, 54, 0, 50), (55, 70, 51, 100), (71, 85, 101, 150), (86, 105, 151, 200), (106, 200, 201, 300),
               (float('inf'), float('inf'), 301, 500)],
    "O3_1hr": [(0, float('inf'), 0, 50), (125, 164, 51, 100), (165, 204, 101, 150), (205, 404, 151, 200),
               (405, 604, 201, 300), (float('inf'), float('inf'), 301, 500)],
    "PM25_24hr": [(0.0, 9.0, 0, 50), (9.1, 35.4, 51, 100), (35.5, 55.4, 101, 150), (55.5, 125.4, 151, 200),
                  (125.5, 225.4, 201, 300), (225.5, 325.4, 301, 500)],
    "PM10_24hr": [(0.0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150), (255, 354, 151, 200),
                  (355, 424, 201, 300), (425, float('inf'), 301, 500)],
    "CO_8hr": [(0.0, 4.4, 0, 50), (4.5, 9.4, 51, 100), (9.5, 12.4, 101, 150), (12.5, 15.4, 151, 200),
               (15.5, 30.4, 201, 300), (30.5, 50.4, 301, 500)],
    "SO2_1hr": [(0.0, 35, 0, 50), (36, 75, 51, 100), (76, 185, 101, 150), (186, 304, 151, 200),
                (305, 604, 201, 300), (605, 1004, 301, 500)],
    "SO2_24hr": [(0.0, 53, 0, 50), (54, 100, 51, 100), (101, 360, 101, 150), (361, 649, 151, 200),
                 (650, 1249, 201, 300), (1250, float('inf'), 301, 500)],
    "NO2_1hr": [(0.0, 50, 0, 50), (51, 100, 51, 100), (101, 360, 101, 150), (361, 649, 151, 200),
                (650, 1249, 201, 300), (1250, float('inf'), 301, 500)]
}


# Function to add data
def add_location(name, latitude, longitude):
    existing_location = session.query(Location).filter(Location.name == name).first()
    if existing_location:
        print(f"Location '{name}' already exists.")
        return existing_location
    else:
        location = Location(name=name, latitude=latitude, longitude=longitude)
        session.add(location)
        session.commit()
        print(f"Location '{name}' added successfully.")
        return location


def add_parameter(name, unit):
    existing_parameter = session.query(Parameter).filter(Parameter.name == name).first()
    if existing_parameter:
        print(f"Parameter '{name}' already exists.")
        return existing_parameter
    else:
        parameter = Parameter(name=name, unit=unit)
        session.add(parameter)
        session.commit()
        print(f"Parameter '{name}' added successfully.")
        return parameter


def add_measurement(location_id, parameter_id, value):
    measurement = Measurement(location_id=location_id, parameter_id=parameter_id, value=value)
    session.add(measurement)
    session.commit()


# returns all sensor_name + sensor_coordinates
def get_all_sensor_geo():
    sensor_locations = session.query(Location).all()
    return sensor_locations


# returns a list of tuples where each tuple contains the sensor name and its corresponding location ID
def get_sensor_locations():
    sensor_locations = session.query(Location.name, Location.id).all()
    return sensor_locations


# returns a list of sensor names
def get_all_sensor_names():
    sensor_names = session.query(Location.name).all()
    return [name for name, in sensor_names]


# sensor_name exists - its location_id
# sensor_name NOT exists - None
def get_location_id_by_sensor_name(sensor_name):
    location_id = session.query(Location.id).filter(Location.name == sensor_name).scalar()
    return location_id


# Function to calculate AQI for individual pollutant
def calculate_aqi_for_pollutant(pollutant, concentration):
    for low, high, Ilow, Ihigh in breakpoints[pollutant]:
        if low <= concentration <= high:
            return ((Ihigh - Ilow) / (high - low)) * (concentration - low) + Ilow
    return 0  # If concentration is out of range


# Method to add AQI result to database
def add_aqi_result(location_id, aqi_value):
    aqi_result = AQIResult(location_id=location_id, aqi_value=aqi_value)
    session.add(aqi_result)
    session.commit()


# Method to add AQI per pollutant result to database
def add_aqi_pollutant_result(location_id, pollutant_name, aqi_value):
    aqi_result = AQIPollutantResult(location_id=location_id, pollutant_name=pollutant_name,
                                    aqi_value=aqi_value)
    session.add(aqi_result)
    session.commit()


# Method to Calculate AQI
def calculate_aqi(pm25, pm10, co, o3, so2, no2):
    # AQI calculation logic
    # Implement AQI calculation based on pollutant concentrations
    # Return the calculated AQI value
    # You can use standard AQI calculation formulas or lookup tables

    # Calculate AQI for each pollutant
    aqi_values = [
        calculate_aqi_for_pollutant("O3_8hr", o3),
        calculate_aqi_for_pollutant("PM25_24hr", pm25),
        calculate_aqi_for_pollutant("PM10_24hr", pm10),
        calculate_aqi_for_pollutant("CO_8hr", co),
        calculate_aqi_for_pollutant("SO2_1hr", so2),
        calculate_aqi_for_pollutant("NO2_1hr", no2)
    ]

    # Return the maximum AQI value
    return int(max(aqi_values)), aqi_values
