from model.UserAgent import UserAgent
from model.Cookie import Cookie
from model.models import Place, DirectFlightTicket, FlightResult

from requests import Session
from datetime import datetime, timezone
from math import ceil
import json

def getInformationFromSegment(segments:list)->dict:
    time_format = "%Y-%m-%dT%H:%M:%S"
    arrival = True
    time_list = []
    
    duration_list = []
    transfer_duration_list = []
    stop_list = []
    carrier_set = set()
    flight_number_list = []
    
    for segment in segments:
        duration_list.append(segment["durationInMinutes"])
        
        if arrival:
            time_list.append(datetime.strptime(segment["arrival"], time_format))
        else:
            time_list.append(datetime.strptime(segment["departure"], time_format))
        arrival = not arrival
        
        if len(duration_list)>1: stop_list.append(segment["origin"]["name"])
        
        carrier_set.add(segment["marketingCarrier"]["name"])
        flight_number_list.append(f"{segment['marketingCarrier']['displayCode']}{segment['flightNumber']}")
            
        
    for i in range(1, len(time_list)):
        minute_diff = int(ceil((time_list[i] - time_list[i-1]).total_seconds()/60))
        transfer_duration_list.append(minute_diff)
        
    return {
        "duration_list": duration_list,
        "total_transfer": sum(transfer_duration_list),
        "transfer_duration_list": transfer_duration_list,
        "stop_count": len(stop_list),
        "stop_list": stop_list,
        "carrier_count":  len(carrier_set),
        "carrier_list": list(carrier_set),
        "flight_number_list": flight_number_list
    }

def createAgentDic(agents:list)->dict:
    agent_dic = dict()
    for agent in agents:
        agent_dic[agent["id"]] = {
            "name": agent["name"],
            "isCarrier": agent["isCarrier"],
            "rating": agent["rating"]
        }
    return agent_dic

def getPriceAgentURLInformation(pricingOptions:list, agent_dic:dict)->tuple:
    price_list = []
    agent_list = []
    url_list = []
    isCarrier_list = []
    agent_rating_list = []
    base_url = "https://www.skyscanner.com"
    for option in pricingOptions:
        price = int(ceil(option["price"]["amount"]))
        agent_id = option["agentIds"][0]
        if price>0:
            price_list.append(price)
            agent_list.append(agent_dic[agent_id]["name"])
            url_list.append(f"{base_url}{option['items'][0]['url']}")
            isCarrier_list.append(agent_dic[agent_id]["isCarrier"])
            agent_rating_list.append(agent_dic[agent_id]["rating"])
    
    return price_list, agent_list, url_list, isCarrier_list, agent_rating_list

def getCurrentUTCTime()->str:
    time_format = "%Y-%m-%dT%H:%M:%S"
    now = datetime.now().astimezone()
    now_utc = now.astimezone(timezone.utc)
    return now_utc.strftime(time_format)
    
class FlightScraper:
    def __init__(self, user_agent:UserAgent=None, cookie:Cookie=None, session:Session=None):
        if user_agent is None: raise ValueError("Missing user_agent parameter!")
        self.user_agent = user_agent
        if cookie is None: raise ValueError("Missing cookie parameter!")
        self.cookie = cookie
        if session is None: raise ValueError("Missing session parameter!")
        self.session = session
        return
    
    def get_data(self, origin_entity_id:str, destination_entity_id:str,
                 go_year:int=None, go_month:int=None, go_day:int=None,
                 back_year:int=None, back_month:int=None, back_day:int=None)->dict:
        
        if (origin_entity_id is None or destination_entity_id is None or go_year is None or go_month is None or go_day is None): 
            raise ValueError("Missing standard parameters!")
        
        if (back_year is None or back_month is None or back_day is None): roundTrip = False
        else: roundTrip = True
        
        
        api_url = "https://www.skyscanner.com/g/radar/api/v2/web-unified-search/"

        if roundTrip:
            payload = {
                "cabinClass": "ECONOMY",
                "childAges": [],
                "adults": 1,
                "legs": [
                    {
                        "legOrigin": {
                            "@type": "entity",
                            "entityId": origin_entity_id
                        },
                        "legDestination": {
                            "@type": "entity",
                            "entityId": destination_entity_id
                        },
                        "dates": {
                            "@type": "date",
                            "year": str(go_year),
                            "month": str(go_month),
                            "day": str(go_day)
                        },
                        "placeOfStay": destination_entity_id
                    },
                    {
                        "legOrigin": {
                            "@type": "entity",
                            "entityId": destination_entity_id
                        },
                        "legDestination": {
                            "@type": "entity",
                            "entityId": origin_entity_id
                        },
                        "dates": {
                            "@type": "date",
                            "year": str(back_year),
                            "month": str(back_month),
                            "day": str(back_day)
                        }
                    }
                ]
            }
        else:
            payload = {
                "cabinClass": "ECONOMY",
                "childAges": [],
                "adults": 1,
                "legs": [
                    {
                        "legOrigin": {
                            "@type": "entity",
                            "entityId": origin_entity_id
                        },
                        "legDestination": {
                            "@type": "entity",
                            "entityId": destination_entity_id
                        },
                        "dates": {
                            "@type": "date",
                            "year": str(go_year),
                            "month": str(go_month),
                            "day": str(go_day)
                        },
                        "placeOfStay": destination_entity_id
                    }
                ]
            }

        headers = {
            "accept": "application/json",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "origin": "https://www.skyscanner.com",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "user-agent": self.user_agent.using,
            "x-skyscanner-channelid": "website",
            "x-skyscanner-currency": "USD",
            "x-skyscanner-locale": "en-US",
            "x-skyscanner-market": "US",
            "x-skyscanner-viewid": "f5fd605d-87a5-4c09-a653-676104b162a5",
            "cookie": self.cookie.using
        }
        
        response = self.session.post(api_url, json=payload, headers=headers)
        return response.json()
        
    def clean_data(self, raw_data:dict, skip_complete:bool=False)->list[FlightResult]:
        if not raw_data: raise ValueError("Cannot find any raw data to clean!")
        
        total_results = raw_data["itineraries"]["filterStats"]["total"]
        print(f"Found {total_results} results")
        if total_results==0: return None
        if total_results<10 and not skip_complete: return None
        
        origin_entity_id = raw_data["itineraries"]["filterStats"]["airports"][0]["airports"][0]["entityId"]
        origin_name = raw_data["itineraries"]["filterStats"]["airports"][0]["city"]
        origin_airport_id = raw_data["itineraries"]["filterStats"]["airports"][0]["airports"][0]["id"]
        origin_airport_name = raw_data["itineraries"]["filterStats"]["airports"][0]["airports"][0]["name"]
        
        origin = Place(entity_id = origin_entity_id,
                        name = origin_name,
                        airport_id = origin_airport_id,
                        airport_name = origin_airport_name)
        
        destination_entity_id = raw_data["itineraries"]["filterStats"]["airports"][1]["airports"][0]["entityId"]
        destination_name = raw_data["itineraries"]["filterStats"]["airports"][1]["city"]
        destination_airport_id = raw_data["itineraries"]["filterStats"]["airports"][1]["airports"][0]["id"]
        destination_airport_name = raw_data["itineraries"]["filterStats"]["airports"][1]["airports"][0]["name"]
        
        destination = Place(entity_id = destination_entity_id,
                        name = destination_name,
                        airport_id = destination_airport_id,
                        airport_name = destination_airport_name)
        
        agent_dic = createAgentDic(raw_data["itineraries"]["agents"])
        scrape_result_list = []
        
        roundTrip = len(raw_data["itineraries"]["results"][0]["legs"])>1
        
        if not roundTrip:                            
            for result in raw_data["itineraries"]["results"]:
                total_duration = result["legs"][0]["durationInMinutes"]
                departure_time = result["legs"][0]["departure"]
                arrival_time = result["legs"][0]["arrival"]
                
                segments = result["legs"][0]["segments"]
                segmentInformation_dic = getInformationFromSegment(segments)
                duration_list = segmentInformation_dic["duration_list"]
                total_transfer_duration = segmentInformation_dic["total_transfer"]
                transfer_duration_list = segmentInformation_dic["transfer_duration_list"]
                stop_count = segmentInformation_dic["stop_count"]
                stop_list = segmentInformation_dic["stop_list"]
                carrier_count = segmentInformation_dic["carrier_count"]
                carrier_list = segmentInformation_dic["carrier_list"]
                flight_number_list = segmentInformation_dic["flight_number_list"]
                
                price_list, agent_list, url_list, fromCarrier_list, agent_rating_list = getPriceAgentURLInformation(result["pricingOptions"], agent_dic)
                
                self_transfer = result["isSelfTransfer"]
                
                getTime = getCurrentUTCTime() 
                
                for price, agent, url, fromCarrier, agent_rating in zip(price_list, agent_list, url_list, fromCarrier_list, agent_rating_list):
                    ticket = DirectFlightTicket(
                        origin = origin,
                        destination= destination,
                        total_duration_minute = total_duration,
                        duration_list = duration_list,
                        total_transfer_duration = total_transfer_duration,
                        transfer_duration_list = transfer_duration_list,
                        stop_list = stop_list,
                        stop_count = stop_count,
                        departure_time = departure_time,
                        arrival_time = arrival_time,
                        carrier_list = carrier_list,
                        carrier_count = carrier_count,
                        flight_numbers_list = flight_number_list
                    )
                    
                    scrape_result = FlightResult(
                        outbound=ticket,
                        agent = agent, 
                        agent_rating = agent_rating,
                        price = price,
                        self_transfer = self_transfer,
                        fromCarrier = fromCarrier,
                        getTime = getTime,
                        url = url
                    )
                    
                    scrape_result_list.append(scrape_result)                                       
        else:
            for result in raw_data["itineraries"]["results"]:
                out_total_duration = result["legs"][0]["durationInMinutes"]
                out_departure_time = result["legs"][0]["departure"]
                out_arrival_time = result["legs"][0]["arrival"]

                segments = result["legs"][0]["segments"]
                segmentInformation_dic = getInformationFromSegment(segments)
                out_duration_list = segmentInformation_dic["duration_list"]
                out_total_transfer_duration = segmentInformation_dic["total_transfer"]
                out_transfer_duration_list = segmentInformation_dic["transfer_duration_list"]
                out_stop_count = segmentInformation_dic["stop_count"]
                out_stop_list = segmentInformation_dic["stop_list"]
                out_carrier_count = segmentInformation_dic["carrier_count"]
                out_carrier_list = segmentInformation_dic["carrier_list"]
                out_flight_number_list = segmentInformation_dic["flight_number_list"]
                
                in_total_duration = result["legs"][1]["durationInMinutes"]
                in_departure_time = result["legs"][1]["departure"]
                in_arrival_time = result["legs"][1]["arrival"]

                segments = result["legs"][1]["segments"]
                segmentInformation_dic = getInformationFromSegment(segments)
                in_duration_list = segmentInformation_dic["duration_list"]
                in_total_transfer_duration = segmentInformation_dic["total_transfer"]
                in_transfer_duration_list = segmentInformation_dic["transfer_duration_list"]
                in_stop_count = segmentInformation_dic["stop_count"]
                in_stop_list = segmentInformation_dic["stop_list"]
                in_carrier_count = segmentInformation_dic["carrier_count"]
                in_carrier_list = segmentInformation_dic["carrier_list"]
                in_flight_number_list = segmentInformation_dic["flight_number_list"]
                
                price_list, agent_list, url_list, fromCarrier_list, agent_rating_list = getPriceAgentURLInformation(result["pricingOptions"], agent_dic)

                self_transfer = result["isSelfTransfer"]
                
                getTime = getCurrentUTCTime() 
                
                for price, agent, url, fromCarrier, agent_rating in zip(price_list, agent_list, url_list, fromCarrier_list, agent_rating_list):
                    out_ticket = DirectFlightTicket(
                        origin = origin,
                        destination= destination,
                        total_duration_minute = out_total_duration,
                        duration_list = out_duration_list,
                        total_transfer_duration = out_total_transfer_duration,
                        transfer_duration_list = out_transfer_duration_list,
                        stop_list = out_stop_list,
                        stop_count = out_stop_count,
                        departure_time = out_departure_time,
                        arrival_time = out_arrival_time,
                        carrier_list = out_carrier_list,
                        carrier_count = out_carrier_count,
                        flight_numbers_list = out_flight_number_list
                    )
                    
                    in_ticket = DirectFlightTicket(
                        origin = destination,
                        destination= origin,
                        total_duration_minute = in_total_duration,
                        duration_list = in_duration_list,
                        total_transfer_duration = in_total_transfer_duration,
                        transfer_duration_list = in_transfer_duration_list,
                        stop_list = in_stop_list,
                        stop_count = in_stop_count,
                        departure_time = in_departure_time,
                        arrival_time = in_arrival_time,
                        carrier_list = in_carrier_list,
                        carrier_count = in_carrier_count,
                        flight_numbers_list = in_flight_number_list
                    )
                    
                    scrape_result = FlightResult(
                        outbound = out_ticket,
                        inbound = in_ticket,
                        agent = agent, 
                        agent_rating = agent_rating,
                        price = price,
                        self_transfer = self_transfer,
                        fromCarrier = fromCarrier,
                        getTime = getTime,
                        url = url
                    )
                    
                    scrape_result_list.append(scrape_result) 
                            
        return scrape_result_list