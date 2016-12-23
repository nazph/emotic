import json
from .base_test_case import BaseTestCase
from .utils import TestUtils


class TestSignUp(BaseTestCase):

    # Do not sign in automatically
    username = None

    def browse_to_sign_up(self):
        '''
        Browses to the sign up page
        '''
        self.driver.get(self.emotiv_url)
        self.driver.find_element_by_link_text('Sign Up').click()
        self.assertIn('If you already have an EmotivID', self.driver.page_source)

    def select_builder(self):
        '''
        Clicks the button that identifies this account as a builder
        '''
        self.driver.find_element_by_xpath('//label[contains(., "Build")]').click()

    def input_new_org_name(self):
        '''
        Inputs a new, random name as the builder's organization
        '''
        self.driver.find_element_by_id("organization_name-ddbutton").click()
        self.driver.find_element_by_id("organization_name-ddtext0").click()
        self.driver.find_element_by_id("new_org_name").clear()
        self.driver.find_element_by_id("new_org_name").send_keys("auto" + TestUtils.generate_unique_key())

    def test_emotiv_error_message(self):
        '''
        Verify that the emotiv error message is not JSON
        '''
        self.browse_to_sign_up()

        username, email = TestUtils.generate_unique_credentials()

        self.driver.find_element_by_name('username').send_keys('emotiv.auto.builder.1blkja')
        self.driver.find_element_by_name('password').send_keys(self.default_password)
        self.driver.find_element_by_name('first_name').send_keys('Emotiv')
        self.driver.find_element_by_name('last_name').send_keys('Auto')
        self.driver.find_element_by_name('email').send_keys('emotiv.auto+hash@gmail.com')
        self.select_builder()
        self.input_new_org_name()

        self.driver.find_element_by_name('login').click()

        # The error message should not be json
        self.assertRaises(ValueError, json.loads, self.driver.find_element_by_css_selector('li.error').text)

    def test_new_builder_new_email_new_org(self):
        '''
        Creates a new builder with their own organization
        '''
        self.browse_to_sign_up()

        username, email = TestUtils.generate_unique_credentials()

        self.driver.find_element_by_name('username').send_keys(username)
        self.driver.find_element_by_name('password').send_keys(self.default_password)
        self.driver.find_element_by_name('first_name').send_keys('Emotiv')
        self.driver.find_element_by_name('last_name').send_keys('Auto')
        self.driver.find_element_by_name('email').send_keys(email)
        self.select_builder()
        self.input_new_org_name()

        self.driver.find_element_by_name('login').click()

        self.assert_in_flashes('Please confirm your email address first')

    def test_new_builder_new_email_existing_org(self):
        '''
        Creates a new builder with an existing organization
        '''
        self.browse_to_sign_up()

        username, email = TestUtils.generate_unique_credentials()

        self.driver.find_element_by_name('username').send_keys(username)
        self.driver.find_element_by_name('password').send_keys(self.default_password)
        self.driver.find_element_by_name('first_name').send_keys('Emotiv')
        self.driver.find_element_by_name('last_name').send_keys('Auto')
        self.driver.find_element_by_name('email').send_keys(email)

        self.select_builder()
        self.driver.find_element_by_id("organization_name-ddbutton").click()
        self.driver.find_element_by_id("organization_name-ddtext3").click()

        self.driver.find_element_by_name('login').click()

        self.assert_in_flashes('Please confirm your email address first')

    def test_new_viewer_new_email(self):
        '''
        Creates a new viewer with a new email
        '''
        self.browse_to_sign_up()

        username, email = TestUtils.generate_unique_credentials()

        self.driver.find_element_by_name('username').send_keys(username)
        self.driver.find_element_by_name('password').send_keys(self.default_password)
        self.driver.find_element_by_name('first_name').send_keys('Emotiv')
        self.driver.find_element_by_name('last_name').send_keys('Auto')
        self.driver.find_element_by_name('email').send_keys(email)

        self.driver.find_element_by_name('login').click()

        self.assert_in_flashes('Please confirm your email address first')

    def test_existing_email(self):
        '''
        Attempts to create a new viewer with an existing email
        '''
        self.browse_to_sign_up()

        username, email = TestUtils.generate_unique_credentials()

        self.driver.find_element_by_name('username').send_keys(username)
        self.driver.find_element_by_name('password').send_keys(self.default_password)
        self.driver.find_element_by_name('first_name').send_keys('Emotiv')
        self.driver.find_element_by_name('last_name').send_keys('Auto')
        self.driver.find_element_by_name('email').send_keys('emotiv.auto@gmail.com')

        self.driver.find_element_by_name('login').click()

        self.assertIn('There is an EmotivID associated with that email account',
            self.driver.find_element_by_css_selector('li.error').text)
