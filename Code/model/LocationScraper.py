from model.UserAgent import UserAgent

from requests import Session
from requests import Session

def getSearchString(name:str):
    ls = name.split(" ")
    return "%20".join(ls)

def getStringOrNA(string:str):
    return string if string else "N/A"

class LocationScraper:
    def __init__(self, user_agent:UserAgent, session:Session):
        if user_agent is None: raise ValueError("Missing user_agent parameter!")
        self.user_agent = user_agent
        if session is None: raise ValueError("Missing session parameter!")
        self.session = session
        
        self.user_agent = user_agent
        self.session = session
        
    def getData(self, name:str)->dict:
        search_string = getSearchString(name)
        url = f"https://www.skyscanner.com/g/autosuggest-search/api/v1/search-flight/US/en-US/{search_string}"

        querystring = {"isDestination":"false","enable_general_search_v2":"true","autosuggestExp":""}

        headers = {
            "accept": "application/json",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "pagetype": "HOME_PAGE",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "skyscanner-client-name": "banana",
            "user-agent": self.user_agent.using
        }

        response = self.session.get(url=url, headers=headers, params=querystring)
        json_data = response.json()
        return json_data[0] if len(json_data)>0 else None
    
    def getDescription(self, raw_data:dict)->dict:
        if "Tags" in raw_data:
            if raw_data["Tags"][0]=="NEARBY_CITY":
                dic = {
                    "airport_code": getStringOrNA(raw_data["IataCode"]),
                    "airport_name": "[WARNING] This is not an airport but a place: " + getStringOrNA(raw_data["ResultingPhrase"]),
                    "country":  getStringOrNA(raw_data["CountryName"]),
                    "entity_code": getStringOrNA(raw_data["GeoId"])
                }
            else:
                dic = {
                    "airport_code": getStringOrNA(raw_data["AirportInformation"]["PlaceId"]),
                    "airport_name": getStringOrNA(raw_data["AirportInformation"]["PlaceName"]),
                    "country":  getStringOrNA(raw_data["CountryName"]),
                    "entity_code": getStringOrNA(raw_data["AirportInformation"]["GeoId"])
                }
        else: 
            dic = {
                "airport_code": getStringOrNA(raw_data["PlaceId"]),
                "airport_name": getStringOrNA(raw_data["PlaceName"]),
                "country":  getStringOrNA(raw_data["CountryName"]),
                "entity_code": getStringOrNA(raw_data["GeoId"])
            }
        return dic

    def getCoordinate(self, raw_data:dict)->tuple[float, float]:
        if "Tags" in raw_data and raw_data["Tags"][0]!='NEARBY_CITY':
            cor_string = raw_data["AirportInformation"]["Location"]
        else: 
            cor_string = raw_data["Location"]
        
        lat, lon = tuple(map(float, cor_string.split(",")))
        
        return lat, lon