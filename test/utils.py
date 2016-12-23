import os
import time
import shutil
from datetime import datetime, timedelta

from selenium.common.exceptions import TimeoutException, NoAlertPresentException, NoSuchElementException
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

class TestUtils(object):

    test_path = os.path.join(os.getcwd(), 'test_files')
    temp_path = os.path.join(test_path, 'temp')
    results_path = os.path.join(os.getcwd(), 'results')

    @staticmethod
    def ensure_logged_in(driver, username, emotiv_url, password):
        '''
        Ensures that we are currently logged in
        '''
        driver.get(emotiv_url)
        try:
            driver.find_element_by_class_name('user_menu')
        except NoSuchElementException:
            TestUtils.login(driver,username, password)

    @staticmethod
    def login(driver, username, password):
        '''
        Login the user given the username
        '''
        username_element = driver.find_element_by_name("username")
        username_element.send_keys(username)
        password_element = driver.find_element_by_name("password")
        password_element.send_keys(password)
        password_element.submit()

    @staticmethod
    def get_todays_date():
        return TestUtils.get_date_from_today()

    @staticmethod
    def get_date_from_today(days=0):
        '''
        Returns the date from today given the days offset
        '''
        return (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

    @staticmethod
    def generate_unique_key():
        '''
        Generates a unique key based on the current timestamp
        '''
        return hex(int(time.time()))[2:]

    @staticmethod
    def create_temp_folder():
        if not os.path.exists(TestUtils.temp_path):
            os.makedirs(TestUtils.temp_path)

    @staticmethod
    def remove_temp_folder():
        if os.path.exists(TestUtils.temp_path):
            shutil.rmtree(TestUtils.temp_path)

    @staticmethod
    def create_results_folder():
        if not os.path.exists(TestUtils.results_path):
            os.makedirs(TestUtils.results_path)

    @staticmethod
    def generate_unique_credentials():
        '''
        Generates a unique username and email for this test run so
        multiple tests can run in parallel
        '''
        unique_key = TestUtils.generate_unique_key()
        username = 'auto.' + unique_key
        email = 'emotiv.auto+{0!s}@gmail.com'.format(unique_key)
        return (username, email)

    @staticmethod
    def select_checkbox_with_text(driver, text):
        driver.find_element_by_xpath('//*[contains(text(), "{0!s}")]'.format(text)).click()

    @staticmethod
    def do_and_confirm(driver, f):
        handles_alerts = driver.desired_capabilities['handlesAlerts']
        if not handles_alerts:
            driver.execute_script("window.confirm = function(){return true;}")
        f()
        if handles_alerts:
            try:
                Alert(driver).accept()
            except NoAlertPresentException:
                pass


class FindElementBy(object):

    @staticmethod
    def any(driver, element, by=By.XPATH, timeout=10):
        '''
        Find an element by xpath (default)
        '''
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.presence_of_element_located((by, element)))

    @staticmethod
    def xpath(driver, element, timeout=10):
        '''
        Find an element by xpath
        '''
        return FindElementBy.any(driver, element, By.XPATH, timeout)

    @staticmethod
    def css_selector(driver, element, timeout=10):
        '''
        Find an element by css selector
        '''
        return FindElementBy.any(driver, element, By.CSS_SELECTOR, timeout)

    @staticmethod
    def id(driver, element, timeout=10):
        '''
        Find an element by id
        '''
        return FindElementBy.any(driver, element, By.ID, timeout)

    @staticmethod
    def class_name(driver, element, timeout=10):
        '''
        Find an element by class name
        '''
        return FindElementBy.any(driver, element, By.CLASS_NAME, timeout)

    @staticmethod
    def name(driver, element, timeout=10):
        '''
        Find an element by name
        '''
        return FindElementBy.any(driver, element, By.NAME, timeout)


class FindElementsBy(object):

    @staticmethod
    def any(driver, element, by=By.XPATH, timeout=10):
        '''
        Find elements by xpath (default)
        '''
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.presence_of_all_elements_located((by, element)))

    @staticmethod
    def xpath(driver, element, timeout=10):
        '''
        Find elements by xpath
        '''
        return FindElementsBy.any(driver, element, By.XPATH, timeout)

    @staticmethod
    def css_selector(driver, element, timeout=10):
        '''
        Find elements by css selector
        '''
        return FindElementsBy.any(driver, element, By.CSS_SELECTOR, timeout)

    @staticmethod
    def class_name(driver, element, timeout=10):
        '''
        Find elements by class name
        '''
        return FindElementsBy.any(driver, element, By.CLASS_NAME, timeout)


def wait_until_element_deleted(driver, element, timeout=10):
    '''
    This waits until an element is removed from the DOM or timesout
    '''
    wait = WebDriverWait(driver, timeout)
    wait.until(EC.staleness_of(element))


def dismiss_alert_if_open(driver, timeout=3):
    try:
        if driver.desired_capabilities['handlesAlerts']:
            WebDriverWait(driver, timeout).until(EC.alert_is_present())
            Alert(driver).dismiss()
    except TimeoutException:
        pass
