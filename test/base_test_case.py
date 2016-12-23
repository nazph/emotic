import sys
import unittest
import logging
from selenium import webdriver
from .utils import TestUtils, FindElementsBy
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

# Only display possible problems
selenium_logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
selenium_logger.setLevel(logging.WARNING)


class BaseTestCase(unittest.TestCase):
    '''
    Base test case to use for all tests
    '''

    # URL to test against
    emotiv_url = "https://emotiv-builder-and-viewer.herokuapp.com"

    # Default password used for all accounts
    default_password = 'Testing1@'

    # This will contain the unique username if the above is True
    username = 'emotiv_auto'

    # Webdriver to use
    driver_factory = webdriver.PhantomJS

    @classmethod
    def setUpClass(cls):
        '''
        Opens the browser to use for this test case and sets up temp files
        '''
        cls.driver = cls.driver_factory()
        # For remote debugging, uncomment this line:
        # cls.driver = cls.driver_factory(service_args=['--remote-debugger-port=9000'])
        cls.driver.set_window_size(1440, 900)
        cls.driver.implicitly_wait(5) # seconds
        cls.driver.get(cls.emotiv_url)

        TestUtils.create_temp_folder()
        TestUtils.create_results_folder()

    @classmethod
    def tearDownClass(cls):
        '''
        Closes the browser for this test case
        '''
        cls.driver.quit()
        TestUtils.remove_temp_folder()

    def setUp(self):
        '''
        Called before every test within the test case
        '''
        if self.username is not None:
            self.ensure_logged_in(self.username)

    def tearDown(self):
        '''
        Called after every test within the test case
        '''
        if sys.exc_info()[0]:
            self.take_screen_shot()

    def take_screen_shot(self, name=None):
        '''
        Takes a screen shot and prepends the name if provided
        '''
        location = TestUtils.results_path + '/'
        if name is not None:
            location = location + name + '_'
        location = location + self.id() + '.png'
        self.driver.save_screenshot(location)

    @classmethod
    def register_user_for_class(cls):
        '''
        Registers a user for the entire test case
        '''
        cls.driver.find_element_by_link_text('Sign Up').click()
        assert 'If you already have an EmotivID' in cls.driver.page_source

        cls.username, cls.email = TestUtils.generate_unique_credentials()

        cls.driver.find_element_by_name('username').send_keys(cls.username)
        cls.driver.find_element_by_name('password').send_keys(cls.default_password)
        cls.driver.find_element_by_name('first_name').send_keys('Emotiv')
        cls.driver.find_element_by_name('last_name').send_keys('Auto')
        cls.driver.find_element_by_name('email').send_keys(cls.email)

        cls.driver.find_element_by_xpath("//div[9]/label/span").click()
        cls.driver.find_element_by_id("organization_name-ddbutton").click()
        cls.driver.find_element_by_id("organization_name-ddtext0").click()
        cls.driver.find_element_by_id("new_org_name").clear()
        cls.driver.find_element_by_id("new_org_name").send_keys("auto+" + TestUtils.generate_unique_key())

        cls.driver.find_element_by_name('login').click()

        assert 'experiments' in cls.driver.current_url

    def login(self, username, password=default_password):
        '''
        Login the user given the username
        '''
        TestUtils.login(
            self.driver, username, password)
        self.assertNotIn('Login failed', self.driver.page_source)

    def ensure_logged_in(self, username):
        '''
        Ensures that we are currently logged in
        '''
        TestUtils.ensure_logged_in(
            self.driver,
            username,
            self.emotiv_url,
            self.default_password)

    def logout(self):
        '''
        Log out the user
        '''
        try:
            self.show_user_menu()
        except NoSuchElementException:
            return
        self.driver.find_element_by_link_text('Logout').click()

    def browse_to_user_settings(self):
        '''
        Browses to the user settings page
        '''
        self.show_user_menu()
        self.driver.find_element_by_link_text('User Settings').click()
        self.assertIn('Change Attributes', self.driver.page_source)

    def show_user_menu(self):
        '''
        Shows the user menu so we may act upon the drop down list
        '''
        user_menu = self.driver.find_element_by_class_name("user_menu")
        ActionChains(self.driver).move_to_element(user_menu).click().perform()

    def browse_to_change_password(self):
        '''
        Browses to the change password screen
        '''
        self.browse_to_user_settings()
        self.driver.find_element_by_link_text('Password').click()
        self.assertIn('Change Password', self.driver.page_source)

    def assert_in_flashes(self, text, msg='Flash message not found', retry=True):
        '''
        Asserts that the error text is inside the flashes
        '''
        try:
            flashes = FindElementsBy.class_name(self.driver, 'flashes')
            self.assert_(any(text in f.text for f in flashes), msg)
        except NoSuchElementException:
            print('NoSuchElementException')
            self.fail(msg)
        except StaleElementReferenceException:
            if retry:
                self.assert_in_flashes(text, msg=msg, retry=False)
            else:
                raise
