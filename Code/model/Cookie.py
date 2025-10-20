import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep
from random import randrange, randint
from pyautogui import moveTo, doubleClick

"""
1. change cookie periodically would avoid slow request time
2. use another no block cookie would not remove the block => if getting blocked, then need to solve the captcha instead of switching to a new cookie
"""

def solve_captcha():
    time_out = 100
    moveTo(acs_btn_location[0] + randint(-5,5), acs_btn_location[1] + randint(-5,5), duration=1)
    doubleClick()
    
    sleep(time_out)

    moveTo(captcha_btn_location[0] + randint(-5,5), captcha_btn_location[1] + randint(-5,5), duration=0.5)
    doubleClick()
    sleep(3)
    
def solve_captcha_with_link(capcha_link:str):
    
    link = f"https://www.skyscanner.com{capcha_link}"
    
    options = uc.ChromeOptions()
    options.add_argument("--incognito")
    driver = uc.Chrome(
        options=options,
        version_main=139,
        browser_executable_path=r"xxxxxx\chrome.exe"
    )
    driver.get(link)

    WebDriverWait(driver, 60).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    sleep(randrange(3,5))
    solve_captcha()
    driver.close()

target_cookies = set([
    "_pxhd",
    "__Secure-anon_token",
    "__Secure-anon_csrf_token",
    "ssculture",
    "__Secure-ska",
    "device_guid",
    "pxcts",
    "_pxvid",
    "scanner",
    "_px3",
    "QSI_S_ZN_0VDsL2Wl8ZAlxlA",
    "abgroup",
    "jha"
])

acs_btn_location = (806, 761)
captcha_btn_location = (1041, 744)

class Cookie:
    def __init__(self):
        self.using = self.get_cookie()
        
    def get_cookie(self)->str:        
        options = uc.ChromeOptions()
        options.add_argument("--incognito")
        driver = uc.Chrome(
            options=options,
            version_main=139,
            browser_executable_path=r"xxxxxxx\chrome.exe"
        )
        driver.get("https://www.skyscanner.com/")

        WebDriverWait(driver, 60).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        sleep(randrange(3,5))

        url = driver.current_url
        if "captcha" in url: 
            print("Solving captcha...")
            solve_captcha()
            WebDriverWait(driver, 60).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            sleep(randrange(3,5))
            

        cookies = driver.get_cookies()
        
        collector_cookie_dict = {}
        cookie_counter = 0
        
        for cookie in cookies:
            if cookie["name"] in target_cookies:
                collector_cookie_dict[cookie["name"]] = cookie["value"]
                cookie_counter+=1
                
        print(f"Found {cookie_counter}/{len(target_cookies)} cookies")
        
        if  cookie_counter>=len(target_cookies)//2:
            driver.quit()
            cookie_string = "; ".join([f"{name}={value}" for name, value in collector_cookie_dict.items()])
            return cookie_string
        else:
            print("Solving captcha...")
            solve_captcha()
            WebDriverWait(driver, 60).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            sleep(randrange(3,5))
        
        cookies = driver.get_cookies()
        driver.quit()
        
        collector_cookie_dict = {}
        cookie_counter = 0
        
        for cookie in cookies:
            if cookie["name"] in target_cookies:
                collector_cookie_dict[cookie["name"]] = cookie["value"]
                cookie_counter+=1
                
        print(f"Found {cookie_counter}/{len(target_cookies)} cookies")
        
        if cookie_counter>=len(target_cookies)//2:
            cookie_string = "; ".join([f"{name}={value}" for name, value in collector_cookie_dict.items()])
            return cookie_string
        else: raise ValueError("Cannot find cookies!")
        
