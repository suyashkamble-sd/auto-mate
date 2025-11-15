import sys
sys.path.append('..')
import os
# from config.chromeInstance_hm import chromebrowser
from config.chromeInstance_hmuc import chromebrowser
from selenium.webdriver.common.by import By

def start_app(path):
    driver=None
    try:
        os.makedirs(path,exist_ok=True)
        driver=chromebrowser(downloadLocation=path)
        driver.maximize_window()
        driver.get('https://the-internet.herokuapp.com/')
        driver.find_element(By.XPATH,'//a[text()="Basic Auth"]').click()
    except:
        if driver:driver.quit()
if __name__=='__main__':
    path=r'D:\projects\python\RPA\test'
    start_app(path=path)