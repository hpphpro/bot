# dependencies
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
import undetected_chromedriver as uc
# built-in modules
from datetime import datetime
import os, pickle, sys
import logging
import time
# self modules, except loguru
from config.config import NCS_LOGIN, NCS_PASSWORD, INSTA_LOGIN, INSTA_PASSWORD
from config.logguru_log import error, info

logging.getLogger('WDM').setLevel(logging.CRITICAL)

class NCSAuth:
    __slots__ = ('chrome_options', 'path')
    
    def __init__(self) -> None:
        '''Options for chrome that's guarantee clear work'''
        self.chrome_options = uc.ChromeOptions()
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument('--disable-notifications')
        self.chrome_options.add_argument("--disable-popup-blocking")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-infobars")
        self.chrome_options.add_argument("--profile-directory=Default")
        self.chrome_options.add_argument("--ignore-certificate-errors")
        self.chrome_options.add_argument("--disable-plugins-discovery")
        self.chrome_options.add_argument("--prompt-for-external-extensions")
        self.chrome_options.add_argument("--incognito")
        self.chrome_options.add_argument("user_agent=DN")
        self.path = f'{os.getcwd()}\\parser\\source\\' if sys.platform == 'win32' else  f'{os.getcwd()}/parser/source/'

    def authorization(self, url='https://ncs.io') -> None:
        driver = uc.Chrome(headless=True, options=self.chrome_options, service=Service(ChromeDriverManager().install()))
        '''Ncs authorization and fetching it cookies'''
        try:
            info('Authorization to ncs.io')
            driver.get(url)
            driver.implicitly_wait(20)
            WebDriverWait(driver, 15).until(lambda driver: driver.find_element(By.CLASS_NAME, 'panel-btn')).click()

            email = WebDriverWait(driver, 15).until(lambda driver: driver.find_element(By.NAME, 'email'))
            email.clear()
            email.send_keys(NCS_LOGIN) # putting login
            
            time.sleep(0.2)
            log_password = WebDriverWait(driver, 15).until(lambda driver: driver.find_element(By.NAME, 'password'))
            log_password.clear()
            log_password.send_keys(NCS_PASSWORD + Keys.ENTER) # putting password
            
            # wating till element appears to go ahead
            WebDriverWait(driver, 15).until(lambda driver: driver.find_element(By.XPATH, '/html/body/header/nav/ul[1]/li[5]/a/p'))
            os.makedirs(self.path, exist_ok=True)
            with open(f'{self.path}ncs_cookies.pkl', 'wb') as file:
                pickle.dump(driver.get_cookies(), file)

            time_created = datetime.now().strftime('%Y.%m.%d::%H.%M')
            with open(f'{self.path}ncs_log.txt', 'w', encoding='utf-8') as f:
                f.write(time_created)
        except (TimeoutException, NoSuchElementException) as ex:
            error(f'Authorization failed with {ex.__class__.__name__}. Try again')
        else:
            info('Done!')
        finally:
            driver.close()
            driver.quit()
            

    def get_cookie(self) -> dict:
        '''Getting cookies for instagram'''
        cookies = {}
        with open(f'{self.path}ncs_cookies.pkl', 'rb') as file:
            for item in pickle.load(file):
                if 'ncs_session' in item.values():
                    cookies['ncs_session'] = item['value']
                if 'XSRF-TOKEN' in item.values():
                    cookies['XSRF-TOKEN'] = item['value']
            
        return cookies 

class InstagramAuth(NCSAuth):
    __slots__ = ()
    
    def authorization(self, url='https://www.instagram.com/') -> None:
        ''' Instagram authorization and fething cookie'''
        with uc.Chrome(headless=True, service=Service(ChromeDriverManager().install()), options=self.chrome_options) as driver:
            info('Authorization to instagram')
            retry = 1
            while retry < 4:
                driver.get(url)
                driver.implicitly_wait(20)
                
                username = WebDriverWait(driver, 10).until(lambda driver: driver.find_element(By.CSS_SELECTOR, 'input[name="username"]'))
                username.click()
                username.clear()
                username.send_keys(INSTA_LOGIN) # putting username
                
                time.sleep(0.1)
                password = WebDriverWait(driver, 10).until(lambda driver: driver.find_element(By.CSS_SELECTOR, 'input[name="password"]'))
                password.click()
                password.clear()
                password.send_keys(INSTA_PASSWORD + Keys.ENTER) # putting password
                try:
                    # waiting till we get an avatar button
                    WebDriverWait(driver, 10).until(lambda driver: driver.find_element(By.CSS_SELECTOR, 'img[data-testid="user-avatar"]'))
                except (TimeoutException, NoSuchElementException) as ex:
                    # reconnecting if not
                    error(f'Unexpexted error occurred {ex.__class__.__name__}\nReconnecting...{retry}') 
                    retry += 1 
                    driver.refresh()
                    time.sleep(5)
                else:
                    os.makedirs(self.path, exist_ok=True)
                    with open(f'{self.path}insta_cookies.pkl', 'wb') as file:
                        pickle.dump(driver.get_cookies(), file)
                    time_created = datetime.now().strftime('%Y.%m.%d::%H.%M')
                    with open(f'{self.path}insta_log.txt', 'w', encoding='utf-8') as file:
                        file.write(time_created)
                    info('Done!')
                    break
                    
        driver.quit()
    
    
   
    def get_cookie(self) -> dict:
        '''Getting cookies for instagram'''
        cookie_names =  ('mid','ig_did','ig_nrcb','shbid','shbts','datr','csrftoken','ds_user_id' ,'sessionid','rur','datr',) # name's that's we need to clear work
        cookies = {}
        with open(f'{self.path}insta_cookies.pkl', 'rb') as file:
            for cookie_dict in pickle.load(file):
                for name in cookie_names:
                    if name in cookie_dict.values():
                        cookies[name] = cookie_dict['value']
                        break
                        
        return cookies
    

