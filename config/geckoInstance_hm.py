# -*- coding: utf-8 -*-
"""
Created on Feb 24 2026

@author: Suyash.Kamble
Firefox/Gecko RPA browser automation with human-like interactions
"""
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import time
import random
import os
from pdb import set_trace as st


class HumanWebElement(WebElement):
    """
    Custom WebElement that overrides send_keys for human-like typing.
    Compatible with Selenium 4+: __init__(parent, id_).
    """
    def send_keys(self, text, error_rate=0.02, avg_delay=0.1):
        """
        Human-like send_keys: Char-by-char with random delays, occasional backspaces.
        - error_rate: Probability of "mistake" (backspace + re-type char).
        - avg_delay: Average ms between keys (total time ~ len(text) * avg_delay * 2 for realism).
        """
        
        actions = ActionChains(self._parent)  # Parent is driver
        actions.click(self).perform()  # Focus first
        time.sleep(random.uniform(0.9, 1.5))  # Initial pause

        for char in text:
            # Random delay (normal dist around avg_delay)
            delay = max(0.01, random.uniform(avg_delay, avg_delay * 0.3))  # 0.01-0.3s typical
            time.sleep(delay)
            actions.send_keys(char)

            # Occasional "mistake": Backspace + re-type (1-5% chance)
            if random.random() < error_rate:
                time.sleep(random.uniform(0.05, 0.15))  # Hesitation
                actions.send_keys(Keys.BACKSPACE)
                time.sleep(random.uniform(0.1, 0.25))  # Pause after error
                # Re-type the char (with shift if needed)
                if char.isupper() or char in '!@#$%^&*()_+{}|:"<>?':
                    actions.key_down(Keys.SHIFT).send_keys(char.lower() if char.isupper() else char).key_up(Keys.SHIFT)
                else:
                    actions.send_keys(char)
                print(f"💭 Human 'mistake' corrected: {char}")

            actions.perform()  # Batch actions for smoothness
            actions = ActionChains(self._parent)  # Reset chain

        # Final "settle" pause
        time.sleep(random.uniform(0.2, 0.5))


class geckobrowser(webdriver.Firefox):
    """
    RPA-optimized Firefox WebDriver: Hooks + human-like send_keys via custom elements.
    Usage: elem = driver.find_element(...); elem.send_keys("Hello World")  # Now human-like!
    Python 3.9+ & Selenium 4+ compatible.
    """

    def __init__(self,
                     downloadLocation=None,
                     use_proxy=False,
                     service=None,
                     before_find=None,
                     after_find=None,
                     on_failure=None,
                     geckodriver_path=None,
                     *args, **kwargs):
            # st()
            # Set default download path if not provided
            self.downloadLocation = os.path.abspath(downloadLocation or os.path.join(os.getcwd(), "downloads"))
            os.makedirs(self.downloadLocation, exist_ok=True)

            self.use_proxy = use_proxy
            self.before_find = before_find or (lambda by, value: None)
            self.after_find = after_find or (lambda by, value, result: None)
            self.on_failure = on_failure or (lambda by, value, exc: None)
            self.geckoDriverPath = os.path.join(os.path.dirname(os.path.abspath(__file__)),'drivers')
            os.makedirs(self.geckoDriverPath, exist_ok=True)

            # Firefox options setup
            self.firefox_options = Options()

            # Set download preferences
            self.firefox_options.set_preference("browser.download.folderList", 2)  # Custom folder
            self.firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
            self.firefox_options.set_preference("browser.download.dir", self.downloadLocation)
            self.firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", 
                                                "application/pdf,application/x-pdf,text/csv,application/vnd.ms-excel")
            self.firefox_options.set_preference("pdfjs.disabled", True)  # Don't show PDF in browser
            self.firefox_options.set_preference("print.print_to_file", True)
            self.firefox_options.set_preference("print.printer_Mozilla_Save_to_PDF.print_to_file", True)
            self.firefox_options.set_preference("print.printer_Mozilla_Save_to_PDF.print_to_filename", 
                                                os.path.join(self.downloadLocation, "output.pdf"))

            # Performance & stealth
            self.firefox_options.add_argument('--disable-gpu')
            self.firefox_options.add_argument('--no-sandbox')
            self.firefox_options.set_preference("dom.webdriver.enabled", False)
            self.firefox_options.set_preference("useAutomationExtension", False)

            if self.use_proxy:
                proxy = "http://your-proxy-server:port"
                # Set Firefox proxy
                self.firefox_options.set_preference("network.proxy.type", 1)  # Manual proxy
                self.firefox_options.set_preference("network.proxy.http", proxy.split(":")[-2].replace("//", ""))
                self.firefox_options.set_preference("network.proxy.http_port", int(proxy.split(":")[-1]))

            # Use provided service or default to GeckoDriverManager
            if geckodriver_path and os.path.exists(geckodriver_path):
                # Use custom path
                self.service = Service(geckodriver_path)
            else:
                # Auto-manage driver
                self.service = Service(GeckoDriverManager().install())
                
            super().__init__(service=self.service, options=self.firefox_options, *args, **kwargs)

    def _execute_find(self, by, value, timeout=20, retry_count=3, single=True):
        """Internal: Core find with wait/retry. Returns HumanWebElement for singles."""
        # Custom conditions using super().find_* to avoid recursion during polling
        if single:
            def wait_condition(driver):
                try:
                    elem = super(geckobrowser, self).find_element(by, value)  # Fixed: self for super call
                    return elem
                except NoSuchElementException:
                    return False
        else:
            def wait_condition(driver):
                try:
                    elems = super(geckobrowser, self).find_elements(by, value)
                    return len(elems) > 0
                except:
                    return False

        for attempt in range(retry_count + 1):
            try:
                self.before_find(by, value)

                if timeout > 0:
                    waiter = WebDriverWait(self, timeout)
                    if single:
                        base_elem = waiter.until(wait_condition)
                        # FIXED: Only parent, id_ (Selenium 4+ signature)
                        element = HumanWebElement(self, base_elem.id)
                        # Apply scroll/hover to wrapped element
                        self.execute_script(
                            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element
                        )
                        time.sleep(random.uniform(1.2, 1.99))
                        actions = ActionChains(self)
                        actions.move_to_element(element).perform()
                    else:
                        waiter.until(wait_condition)
                        base_elems = super().find_elements(by, value)
                        # FIXED: Only parent, id_ for each
                        element = [HumanWebElement(self, e.id) for e in base_elems]
                else:
                    if single:
                        base_elem = super().find_element(by, value)
                        # FIXED: Only parent, id_
                        element = HumanWebElement(self, base_elem.id)
                        # Apply actions
                        self.execute_script(
                            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element
                        )
                        time.sleep(random.uniform(1.2, 1.99))
                        actions = ActionChains(self)
                        actions.move_to_element(element).perform()
                    else:
                        base_elems = super().find_elements(by, value)
                        # FIXED: Only parent, id_
                        element = [HumanWebElement(self, e.id) for e in base_elems]

                if not element:
                    raise NoSuchElementException(f"No { 'element' if single else 'elements' } found.")

                self.after_find(by, value, element)
                return element

            except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as exc:
                if attempt < retry_count:
                    self.on_failure(by, value, exc)
                    time.sleep(random.uniform(0.99, 1.4))
                    continue
                self.on_failure(by, value, exc)
                raise

    def human_send_keys(self, element, text, error_rate=0.02, avg_delay=0.1):
        """Convenience: Human-like typing on any WebElement."""
        # FIXED: Temp wrapper with correct args
        if not isinstance(element, HumanWebElement):
            temp_wrapper = HumanWebElement(element._parent, element.id)
            temp_wrapper.send_keys(text, error_rate, avg_delay)
        else:
            element.send_keys(text, error_rate, avg_delay)

    def find_element(self, by=By.ID, value=None, timeout=20, retry_count=3):
        return self._execute_find(by, value, timeout, retry_count, single=True)

    def find_elements(self, by=By.ID, value=None, timeout=20, retry_count=3):
        return self._execute_find(by, value, timeout, retry_count, single=False)

    def __getattr__(self, name):
        return getattr(super(), name)
