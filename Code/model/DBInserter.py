from requests import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session as DBSession
from os import getenv
from sqlalchemy.engine import URL
from sqlalchemy import create_engine, select
from timezonefinder import TimezoneFinder
import subprocess
from time import sleep
from pyautogui import moveTo, doubleClick

from model.LocationScraper import LocationScraper
from model.db_models import DB_Direct_Flight, DB_Round_Flight, DB_Location, DB_Airport
from model.UserAgent import UserAgent
from model.models import FlightResult


def start_docker_desktop():
    wait_time = 60*10
    
    path = r"xxxxxxxxx\Docker Desktop.exe"
    subprocess.Popen([path])
    
    sleep(wait_time)
    
    moveTo(1741, 436, duration=1)
    doubleClick()

    sleep(wait_time)
    return True

def createDBSession():
    url = URL.create(
        drivername="mysql+pymysql",
        username=getenv("DB_USER"),
        password=getenv("DB_PASS")[::-1],
        host="localhost",
        port=10000,
        database="flight"
    )
    
    engine = create_engine(url=url)
    Session = sessionmaker(bind=engine)
    
    return Session()

def start_docker_container():
    path = r"xxxxxxx\mysql.yml"
    wait_time = 60*10
    result = subprocess.run(
        [r"xxxxxxxxxxxxxxxxxx\docker-compose.exe", "-f", path, "up", "-d"],
        check=True,      # Raise exception if command fails
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    print("Docker stdout:", result.stdout)
    print("Docker stderr:", result.stderr)
    
    sleep(wait_time)
    
    test_session = createDBSession()
    test_session.close()
    return True

def end_docker_container():
    path = r"xxxxxxxxxxxxxxxxxxxxx\mysql.yml"
    wait_time = 60
        
    result = subprocess.run(
        ["docker-compose", "-f", path, "down"],
        check=True,      # Raise exception if command fails
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    sleep(wait_time)

def end_docker_desktop():
    wait_time = 60
    
    wsl_distributions = ["docker-desktop", "docker-desktop-data"]
    for distro in wsl_distributions:
        result = subprocess.run(
            ["wsl", "-t", distro],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
    windows_processes = ["Docker Desktop.exe", "com.docker.backend.exe"]
    for proc in windows_processes:
        result = subprocess.run(
            ["taskkill", "/F", "/IM", proc],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
    sleep(wait_time)

class DBInserter:
    def __init__(self, user_agent:UserAgent, session:Session, dbSession: DBSession):
        self.dbSession = dbSession
        self.location_scraper = LocationScraper(user_agent=user_agent, session=session)
    
    def close(self):
        self.dbSession.close()    
    
    def getTimeZone(self, airport_code:str):
        tf = TimezoneFinder()
        raw_data = self.location_scraper.getData(airport_code)
        lat, lon = self.location_scraper.getCoordinate(raw_data)
        
        return tf.timezone_at(lat=lat, lng=lon)
    
    def insertLocation(self, result:FlightResult):
        location_id_list = [result.outbound.origin.entity_id, result.outbound.destination.entity_id]
        name_list = [result.outbound.origin.name, result.outbound.destination.name]
        airport_code_list = [result.outbound.origin.airport_id, result.outbound.destination.airport_id]
        
        """
        .execute: Result object
        .scalars() converts rows like [(1,), (3,), (5,)] into a flat iterator: 1, 3, 5.
        .all() convert iterator to a list
        """
        
        stmt = select(DB_Location.id).where(DB_Location.id.in_(location_id_list))
        existing_id = set(self.dbSession.execute(stmt).scalars().all())
        
        insert_list = []
        
        for location_id, name, airport_code in zip(location_id_list, name_list, airport_code_list):  
            if location_id in existing_id: continue
            location = DB_Location(
                id=location_id,
                name=name,
                timezone=self.getTimeZone(airport_code)
            )
            insert_list.append(location)
            
        self.dbSession.add_all(insert_list)
        self.dbSession.commit()
    
    def insertAirport(self, result:FlightResult):
        airport_code_list = [result.outbound.origin.airport_id, result.outbound.destination.airport_id]
        name_list = [result.outbound.origin.airport_name, result.outbound.destination.airport_name]
        location_id_list = [result.outbound.origin.entity_id, result.outbound.destination.entity_id]

        stmt = select(DB_Airport.id).where(DB_Airport.id.in_(airport_code_list))
        existing_code = set(self.dbSession.execute(stmt).scalars().all())
        
        insert_list = []
        
        for code, name, location_id in zip(airport_code_list, name_list, location_id_list):
            if code in existing_code: continue
            airport = DB_Airport(
                id=code,
                name=name,
                location_id=location_id
            )
            insert_list.append(airport)
            
        self.dbSession.add_all(insert_list)
        self.dbSession.commit()
        
    def insertDirectFlight(self, result_list:list[FlightResult]):
        insert_list = []
        
        for result in result_list:
            direct_flight = DB_Direct_Flight(
                origin_airport_code=result.outbound.origin.airport_id,
                destination_airport_code=result.outbound.destination.airport_id,
                total_duration_minute=result.outbound.total_duration_minute,
                duration_list=result.outbound.duration_list,
                total_transfer_minute=result.outbound.total_transfer_duration,
                transfer_duration_list=result.outbound.transfer_duration_list,
                stop_count=result.outbound.stop_count,
                stop_list=result.outbound.stop_list,
                departure_time=result.outbound.departure_time,
                arrival_time=result.outbound.arrival_time,
                carrier_count=result.outbound.carrier_count,
                carrier_list=result.outbound.carrier_list,
                flight_number_list=result.outbound.flight_numbers_list,
                agent=result.agent,
                agent_rating=result.agent_rating,
                price=result.price,
                self_transfer=result.self_transfer,
                from_carrier=result.fromCarrier,
                get_time_utc=result.getTime
            )
            
            insert_list.append(direct_flight)
        
        self.dbSession.add_all(insert_list)
        self.dbSession.commit()   
        
    def insertRoundFlight(self, result_list:list[FlightResult]):
        insert_list = []
        
        for result in result_list:
            round_flight = DB_Round_Flight(
                origin_airport_code=result.outbound.origin.airport_id,
                destination_airport_code=result.outbound.destination.airport_id,
                
                in_total_duration_minute=result.inbound.total_duration_minute,
                in_duration_list=result.inbound.duration_list,
                in_total_transfer_minute=result.inbound.total_transfer_duration,
                in_transfer_duration_list=result.inbound.transfer_duration_list,
                in_stop_count=result.inbound.stop_count,
                in_stop_list=result.inbound.stop_list,
                in_departure_time=result.inbound.departure_time,
                in_arrival_time=result.inbound.arrival_time,
                in_carrier_count=result.inbound.carrier_count,
                in_carrier_list=result.inbound.carrier_list,
                in_flight_number_list=result.inbound.flight_numbers_list,
                
                out_total_duration_minute=result.outbound.total_duration_minute,
                out_duration_list=result.outbound.duration_list,
                out_total_transfer_minute=result.outbound.total_transfer_duration,
                out_transfer_duration_list=result.outbound.transfer_duration_list,
                out_stop_count=result.outbound.stop_count,
                out_stop_list=result.outbound.stop_list,
                out_departure_time=result.outbound.departure_time,
                out_arrival_time=result.outbound.arrival_time,
                out_carrier_count=result.outbound.carrier_count,
                out_carrier_list=result.outbound.carrier_list,
                out_flight_number_list=result.outbound.flight_numbers_list,
                
                agent=result.agent,
                agent_rating=result.agent_rating,
                price=result.price,
                self_transfer=result.self_transfer,
                from_carrier=result.fromCarrier,
                get_time_utc=result.getTime   
            )
            
            insert_list.append(round_flight)
            
        self.dbSession.add_all(insert_list)
        self.dbSession.commit()
                    
    def insertFlight(self, result_list:list[FlightResult]):
        if result_list[0].inbound: self.insertRoundFlight(result_list)
        else: self.insertDirectFlight(result_list)
        