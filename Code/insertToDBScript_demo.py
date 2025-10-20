ori_id = "xxxxxx"
dest_id = "xxxxxx"

go_year = 1900
go_month = 12
go_day = 31

back_year = 2000
back_month = 12
back_day = 31

timeout = 30

###########################################

from model.FlightScraper import FlightScraper
from model.Cookie import Cookie
from model.UserAgent import UserAgent
from model.DBInserter import DBInserter, createDBSession, start_docker_container, start_docker_desktop, end_docker_container, end_docker_desktop

from requests import Session
import time

start_docker_desktop()
start_docker_container()

cookie = Cookie()
ua = UserAgent()
s = Session()

scraper = FlightScraper(cookie=cookie, user_agent=ua, session=s)

db_session = createDBSession()
inserter = DBInserter(user_agent=ua, session=s, dbSession=db_session)

###########################################

raw_data = scraper.get_data(ori_id, dest_id, go_year=go_year, go_month=go_month, go_day=go_day, 
                            back_year=back_year, back_month=back_month, back_day=back_day)
cleaned_data = scraper.clean_data(raw_data)
cter = 0
while cter<2 and not cleaned_data:
    print("Incomplete Data")
    cter+=1
    time.sleep(timeout)
    raw_data = scraper.get_data(ori_id, dest_id, go_year=go_year, go_month=go_month, go_day=go_day, 
                            back_year=back_year, back_month=back_month, back_day=back_day)
    cleaned_data = scraper.clean_data(raw_data)
    
inserter.insertLocation(cleaned_data[0])
inserter.insertAirport(cleaned_data[0])
inserter.insertFlight(cleaned_data)

###########################################

raw_data = scraper.get_data(ori_id, dest_id, go_year=go_year, go_month=go_month, go_day=go_day)
cleaned_data = scraper.clean_data(raw_data)
cter = 0
while cter<2 and not cleaned_data:
    print("Incomplete Data")
    cter+=1
    time.sleep(timeout)
    raw_data = scraper.get_data(ori_id, dest_id, go_year=go_year, go_month=go_month, go_day=go_day)
    cleaned_data = scraper.clean_data(raw_data)
    
inserter.insertFlight(cleaned_data)

###########################################

raw_data = scraper.get_data(dest_id, ori_id, go_year=back_year, go_month=back_month, go_day=back_day)
cleaned_data = scraper.clean_data(raw_data)
cter = 0
while cter<2 and not cleaned_data:
    print("Incomplete Data")
    cter+=1
    time.sleep(timeout)
    raw_data = scraper.get_data(ori_id, dest_id, go_year=go_year, go_month=go_month, go_day=go_day)
    cleaned_data = scraper.clean_data(raw_data)
    
inserter.insertFlight(cleaned_data)

inserter.close()
s.close()
end_docker_container()
end_docker_desktop