import time
from .base_test_case import BaseTestCase
from .utils import TestUtils, FindElementBy, wait_until_element_deleted
from .utils import dismiss_alert_if_open
from .experiment_builder import ExperimentBuilder

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import TimeoutException

class AttributeHelper(object):

    def __init__(self, test):
        self.test = test
        self.driver = test.driver

    def create(self, name, input_type, options=[], submit=True):
        self.driver.get(self.test.emotiv_url + '/admin')
        self.driver.find_element_by_link_text('New Attribute').click()
        self.driver.find_element_by_name('name').send_keys(name)
        self.selectType(input_type)
        for option in options:
            self.addOption(option)
        if submit:
            self.submit()

    def selectType(self, input_type):
        Select(
            self.driver.find_element_by_id('select_input_type')
        ).select_by_visible_text(input_type)

    def addOption(self, text, verify=True):
        self.driver.find_element_by_xpath(
            '//button[contains(., "Add additional text option")]'
        ).click()
        self.driver.find_element_by_xpath(
            '//input[@placeholder="Enter a Value"]'
        ).send_keys(text, Keys.ENTER)
        if verify:
            FindElementBy.xpath(
                self.driver,
                '//div[@class="option_row"]/input[@value="{}"]'.format(text))

    def deleteOption(self, text):
        checkbox = self.driver.find_element_by_xpath(
            '//div[input[@type="checkbox" and @value="{}"]]/label'.format(text)
        )
        checkbox.click()
        wait_until_element_deleted(self.driver, checkbox)

    def submit(self, expect='New attribute created'):
        self.driver.find_element_by_xpath(
            '//input[@value="Create Attribute"]').click()
        if expect:
            self.test.assert_in_flashes(expect)

    def delete(self, name):
        self.driver.get(self.test.emotiv_url + '/admin/view_attributes')
        attribute_links = self.driver.find_elements_by_link_text(name)
        if not attribute_links:
            return
        btns = self.driver.find_elements_by_xpath(
            '//button[contains(@onclick,"{}") and @class="delete_btn"]'.format(
                name))
        self.test.assertEquals(len(btns), 1)
        TestUtils.do_and_confirm(self.driver, lambda: btns[0].click())
        wait_until_element_deleted(self.driver, attribute_links[0])
        self.test.assert_in_flashes('Deleted attribute "{}"'.format(name))


class TestAttribute(BaseTestCase):

    username = 'emotiv_admin'
    attr_name = 'Attribute Test ' + TestUtils.generate_unique_key()

    def setUp(self):
        super(TestAttribute, self).setUp()
        self.attributeHelper = AttributeHelper(self)
        self.attributeHelper.create(self.attr_name, 'Single Select Multiple Choice', submit=False)

    def tearDown(self):
        super(TestAttribute, self).tearDown()
        self.attributeHelper.delete(self.attr_name)

    def verify_in_list(self):
        self.driver.find_element_by_link_text('Back to Attributes').click()
        self.driver.find_element_by_link_text(self.attr_name)

    def find_options(self):
        return self.driver.find_elements_by_class_name('option_row')

    def TestAttributeSameName(self):
        '''
        Verifies two attributes cannot have the same name
        '''
        self.attributeHelper.addOption('Hello')
        self.attributeHelper.submit()
        self.attributeHelper.create(self.attr_name,
            'Single Select Multiple Choice', options=['option a'], submit=False)
        self.attributeHelper.submit(expect='An attribute with this name already exists')

    def TestSingleSelectNoOptions(self):
        '''
        Verify single select with no options
        '''
        self.attributeHelper.submit(expect='Must have at least one option.')

    def TestMultiSelectNoOptions(self):
        '''
        Verify multiple select with no options
        '''
        self.attributeHelper.selectType('Multi Select Multiple Choice')
        self.TestSingleSelectNoOptions()

    def TestSingleSelectOneOption(self):
        '''
        Verify single select with one option
        '''
        self.attributeHelper.addOption('Hello')
        self.attributeHelper.submit()
        self.verify_in_list()

    def TestMultiSelectOneOption(self):
        '''
        Verify multiple select with one option
        '''
        self.attributeHelper.selectType('Multi Select Multiple Choice')
        self.TestSingleSelectOneOption()

    # @skip
    def TestSingleSelectManyOptions(self):
        '''
        Verify single select with 101 options
        '''
        for i in range(101):
            self.attributeHelper.addOption('Option {}'.format(i))
        self.attributeHelper.submit()
        self.verify_in_list()

    # @skip
    def TestMultiSelectManyOptions(self):
        '''
        Verify multiple select with 101 options
        '''
        self.attributeHelper.selectType('Multi Select Multiple Choice')
        self.TestSingleSelectManyOptions()

    def TestSingleSelectDuplicateOptionNames(self):
        '''
        Verify single select with duplicate option names
        '''
        # First option
        self.attributeHelper.addOption('Option')
        self.attributeHelper.addOption('Option', verify=False)

        time.sleep(3)  # Give time for duplicate to show up, if it will.
        self.assertEquals(1, len(self.find_options()))

        self.attributeHelper.submit()
        self.verify_in_list()

    def TestMultiSelectDuplicateOptionNames(self):
        '''
        Verify multiple select with duplicate option names
        '''
        self.attributeHelper.selectType('Multi Select Multiple Choice')
        self.TestSingleSelectDuplicateOptionNames()

    def TestSingleSelectEmptyOption(self):
        '''
        Verify single select with empty option
        '''
        self.attributeHelper.addOption('', verify=False)
        time.sleep(1)
        self.assertEquals(0, len(self.find_options()))

    def TestMultiSelectEmptyOption(self):
        '''
        Verify multiple select with empty option
        '''
        self.attributeHelper.selectType('Multi Select Multiple Choice')
        self.TestSingleSelectEmptyOption()

    def TestSingleSelectLongOption(self):
        '''
        Verify single select with long option
        '''
        self.attributeHelper.addOption("Lorem Ipsum is simply dummy text of the printing and typesett...")
        self.attributeHelper.submit()
        self.verify_in_list()

    def TestMultiSelectLongOption(self):
        '''
        Verify multiple select with long option
        '''
        self.attributeHelper.selectType('Multi Select Multiple Choice')
        self.TestSingleSelectLongOption()

    def TestOpenText(self):
        '''
        Verify open text
        '''
        self.attributeHelper.selectType('Open Text')
        self.attributeHelper.submit()
        self.verify_in_list()

    def TestNumeric(self):
        '''
        Verify numeric
        '''
        self.attributeHelper.selectType('Numeric')
        self.attributeHelper.submit()
        self.verify_in_list()

    def TestDate(self):
        '''
        Verify date
        '''
        self.attributeHelper.selectType('Date')
        self.attributeHelper.submit()
        self.verify_in_list()



class TestRequestAttribute(BaseTestCase):

    username = 'emotiv_auto'


    def setUp(self):
        '''
        Called before every test
        '''
        super(TestRequestAttribute, self).setUp()
        self.builder = ExperimentBuilder(self.driver, self.username)

        key = TestUtils.generate_unique_key()
        self.attr_name = 'Attribute ' + key
        self.experiment = 'Attribute Experiment ' + key

        # https://stackoverflow.com/questions/4504622/a-way-to-output-pyunit-test-name-in-setup
        test_id = self.id().split('.')[-1]

        # First create an experiment with a suggested attribute
        self.builder.new_experiment()
        self.builder.step_1(self.experiment)
        self.builder.step_2()
        self.builder.step_3(suggestion='You should add {}{}'.format(self.attr_name, test_id))
        self.builder.complete_experiment()
        self.logout()

        # Login as the admin
        self.ensure_logged_in('emotiv_admin')

    def tearDown(self):
        '''
        Called after every test
        '''
        super(TestRequestAttribute, self).tearDown()
        self.logout()
        self.ensure_logged_in(self.username)

        self.builder.search_for_experiment(self.experiment)
        experiments = self.builder.get_editable_experiments()
        if len(experiments) == 0:
            return
        self.builder.browse_to_edit_experiment_roadmap(experiments[0])
        self.builder.complete_experiment()
        self.builder.delete_experiment()


    def test_approval(self):
        '''
        Verifies that a builder can request an attribute and an admin can approve it
        '''
        req_attribute = FindElementBy.xpath(self.driver, '//div[contains(text(), "{0}")]'.format(
            self.attr_name))
        button = req_attribute.find_element_by_xpath('../button[contains(text(), "Approve")]')
        # A React function handles this click. Wait until it is loaded before clicking.
        FindElementBy.css_selector(self.driver, '#react_loaded')
        button.click()

        FindElementBy.xpath(self.driver, '//button[@type="submit"]').click()
        self.assert_in_flashes('Attribute request approved')
        self.assert_in_flashes('We emailed the requester to let them know Emotiv has approved their criteria request. Please actually create their requested criteria here')

    def test_deny(self):
        '''
        Verifies that a builder can request an attribute and an admin can deny it
        '''
        req_attribute = FindElementBy.xpath(self.driver, '//div[contains(text(), "{0}")]'.format(
            self.attr_name))
        button = req_attribute.find_element_by_xpath('../button[contains(text(), "Deny")]')
        # A React function handles this click. Wait until it is loaded before clicking.
        FindElementBy.css_selector(self.driver, '#react_loaded')
        button.click()

        FindElementBy.xpath(self.driver, '//button[@type="submit"]').click()
        self.assert_in_flashes('Attribute request denied')



class TestViewerFiltration(BaseTestCase):
    def setUp(self):
        '''
        Called before every test
        '''
        self.key = TestUtils.generate_unique_key()
        self.attr_name = 'Viewer Filtration Attribute ' + self.key
        self.experiment = 'Viewer Filtration ' + self.key
        print(self.attr_name)
        print(self.experiment)

        self.attributeHelper = AttributeHelper(self)
        self.builder = ExperimentBuilder(self.driver, self.username)

        self.ensure_logged_in('emotiv_admin')
        self.attributeHelper.create(self.attr_name,
            'Single Select Multiple Choice', options=['A','B','C'])
        self.logout()

    def tearDown(self):
        dismiss_alert_if_open(self.driver)
        super(TestViewerFiltration, self).tearDown()
        self.logout()
        self.ensure_logged_in('emotiv_admin')
        self.attributeHelper.delete(self.attr_name)

    def do_setup(self, attr_value):
        # Create a new experiment with the new attribute
        self.ensure_logged_in('emotiv_auto')
        self.builder.new_experiment()
        self.builder.step_1(self.experiment)
        self.builder.step_2()
        self.builder.step_3(unselect=[(self.key,'C')])
        self.builder.step_4(attributes=[self.attr_name])
        self.builder.complete_experiment()
        self.builder.create_basic_phase()

        # Submit experiment
        self.builder.submit_experiment()
        self.logout()

        # Approve the experiment
        self.ensure_logged_in('emotiv_admin')
        self.builder.approve_experiment(self.experiment)
        self.assert_in_flashes('Experiment request approved')
        self.logout()

        # Change the viewer's attributes
        self.ensure_logged_in('emotiv_viewer')
        self.builder.view_experiment(self.experiment)
        FindElementBy.xpath(self.driver, '//h2[contains(text(), "You need to fill these in before moving forward")]')
        Select(FindElementBy.name(self.driver, self.attr_name.lower())).select_by_visible_text(attr_value)
        FindElementBy.xpath(self.driver, '//input[@value="Change Attributes"]').click()

    def test_meets_criteria(self):
        '''
        Verify that a viewer can view an experiment where they meet the attribute criteria
        '''
        self.do_setup('B')

        # Verify the viewer now meets the criteria for the experiment
        dismiss_alert_if_open(self.driver)
        FindElementBy.xpath(self.driver, '//h2[contains(text(), "Please adjust your Emotiv")]')

    def test_does_not_meet_criteria(self):
        '''
        Verify that a viewer cannot view an experiment where they do not meet the attribute criteria
        '''
        self.do_setup('C')

        # Verify the error
        self.assert_in_flashes('Your attributes don\'t match the experiment\'s criteria')
        self.assertRaises(TimeoutException, self.builder.view_experiment, self.experiment)

