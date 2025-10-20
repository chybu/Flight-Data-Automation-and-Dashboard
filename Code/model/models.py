from dataclasses import dataclass
from typing import Optional

@dataclass
class Place:
    entity_id: str
    name:str
    airport_id: str
    airport_name: str    

@dataclass
class DirectFlightTicket:
    origin: Place
    destination: Place
    
    total_duration_minute: int
    duration_list: list[int]
    total_transfer_duration: int
    transfer_duration_list: list[int]
    
    stop_list: list[str]
    stop_count: int
    
    departure_time: str # example: "2025-12-13T23:40:00"
    arrival_time: str
    
    carrier_list: list[str]
    carrier_count: int
    flight_numbers_list: list[str]
    def to_dict(self, prefix:str)->dict:
        return {
            f"{prefix}total_duration_minute": self.total_duration_minute,
            f"{prefix}duration_list": ", ".join(map(str, self.duration_list)),
            f"{prefix}total_transfer_duration": self.total_transfer_duration,
            f"{prefix}transfer_duration_list": ", ".join(map(str, self.transfer_duration_list)),
            f"{prefix}stop_list": ", ".join(self.stop_list),
            f"{prefix}stop_count": self.stop_count,
            f"{prefix}departure_time": self.departure_time,
            f"{prefix}arrival_time": self.arrival_time,
            f"{prefix}carrier_list": ", ".join(self.carrier_list),
            f"{prefix}carrier_count": self.carrier_count,
            f"{prefix}flight_number_list": ", ".join(self.flight_numbers_list)
        }
    
@dataclass
class FlightResult:
    outbound: DirectFlightTicket
    agent: str
    agent_rating: int
    price: int   
    self_transfer: bool
    fromCarrier: bool
    getTime: str # the time get the ticket in the same format as flight time and in UTC timezone
    url: str
    inbound: Optional[DirectFlightTicket] = None  # None if one-way
    
    def to_dict(self)->dict:
        dic = {
            "agent": self.agent,
            "agent_rating": self.agent_rating,
            "price": self.price,
            "self_transfer": self.self_transfer,
            "from_Carrier": self.fromCarrier,
            "url": self.url
        }
        dic.update(self.outbound.to_dict("outbound_"))
        if self.inbound is not None: dic.update(self.inbound.to_dict("inbound_"))
        
        return dic