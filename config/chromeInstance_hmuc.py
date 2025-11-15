# -*- coding: utf-8 -*-
"""
Created on Sat Nov 15 17:03:59 2025

@author: suyash
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time, random, os, json


class HumanWebElement(WebElement):
    """Human-like typing element."""
    def send_keys(self, text, error_rate=0.02, avg_delay=0.1):

        actions = ActionChains(self._parent)
        actions.click(self).perform()
        time.sleep(random.uniform(0.5, 1.1))

        for char in text:
            time.sleep(random.uniform(avg_delay * 0.5, avg_delay * 1.4))
            actions.send_keys(char)

            if random.random() < error_rate:
                actions.send_keys(Keys.BACKSPACE)
                time.sleep(random.uniform(0.1, 0.3))
                actions.send_keys(char)

            actions.perform()
            actions = ActionChains(self._parent)

        time.sleep(random.uniform(0.2, 0.6))


class chromebrowser(uc.Chrome):
    """Undetected Chrome with human typing + smart find_element()"""

    def __init__(self,
                 downloadLocation=None,
                 use_proxy=False,
                 before_find=None,
                 after_find=None,
                 on_failure=None):

        self.downloadLocation = os.path.abspath(
            downloadLocation or os.path.join(os.getcwd(), "downloads")
        )
        os.makedirs(self.downloadLocation, exist_ok=True)

        self.use_proxy = use_proxy
        self.before_find = before_find or (lambda by, value: None)
        self.after_find = after_find or (lambda by, value, result: None)
        self.on_failure = on_failure or (lambda by, value, exc: None)

        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        chrome_options.add_argument(f"--download-default-directory={self.downloadLocation}")

        if use_proxy:
            chrome_options.add_argument(f"--proxy-server={use_proxy}")

        super().__init__(options=chrome_options)

    # -------------------------------
    # custom find_element with scroll, hover, retry
    # -------------------------------
    def _execute_find(self, by, value, timeout=20, retry_count=3, single=True):

        def wait_single(driver):
            try:
                return super(chromebrowser, self).find_element(by, value)
            except:
                return False

        def wait_multiple(driver):
            try:
                return len(super(chromebrowser, self).find_elements(by, value)) > 0
            except:
                return False

        for attempt in range(retry_count + 1):
            try:
                self.before_find(by, value)

                waiter = WebDriverWait(self, timeout)
                if single:
                    base_elem = waiter.until(wait_single)
                    element = HumanWebElement(self, base_elem.id)

                    self.execute_script(
                        "arguments[0].scrollIntoView({behavior:'smooth',block:'center'});",
                        element
                    )
                    time.sleep(random.uniform(0.4, 1.2))
                    ActionChains(self).move_to_element(element).perform()

                else:
                    waiter.until(wait_multiple)
                    base_elems = super(chromebrowser, self).find_elements(by, value)
                    element = [HumanWebElement(self, e.id) for e in base_elems]

                self.after_find(by, value, element)
                return element

            except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as exc:
                if attempt < retry_count:
                    self.on_failure(by, value, exc)
                    time.sleep(random.uniform(0.5, 1.0))
                else:
                    raise

    def find_element(self, by=By.ID, value=None, timeout=20, retry_count=3):
        return self._execute_find(by, value, timeout, retry_count, single=True)

    def find_elements(self, by=By.ID, value=None, timeout=20, retry_count=3):
        return self._execute_find(by, value, timeout, retry_count, single=False)
