import sys
sys.path.append('..')
sys.path.append(r'D:\projects\python\RPA\git\repos\auto-mate')
import os
from config.chromeInstance_hm import chromebrowser
from config.geckoInstance_hm import geckobrowser
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

def start_app(path):
    driver=None
    try:
        os.makedirs(path,exist_ok=True)
        # driver=chromebrowser(downloadLocation=path)
        driver=geckobrowser(downloadLocation=path)
        driver.maximize_window()
        driver.get('https://www.flipkart.com/')
        try:
            driver.find_element(By.XPATH,'//span[text()="✕"]').click()
        except:
            pass

        searchBox=driver.find_element(By.XPATH,'//input[@name="q"]')
        searchBox.clear()
        searchBox.send_keys('Mobiles')
        searchBox.send_keys(Keys.ENTER)
        time.sleep(10)
    except:
        if driver:driver.quit()
    finally:
        if driver:driver.quit()
if __name__=='__main__':
    path=r'D:\projects\python\RPA\test'
    start_app(path=path)