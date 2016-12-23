from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from .base_test_case import BaseTestCase
from .experiment_builder import ExperimentBuilder
from .utils import FindElementBy, TestUtils

class TestPhaseCreation(BaseTestCase):

    def setUp(self):
        '''
        Called before every test.
        '''
        super(TestPhaseCreation, self).setUp()
        self.builder = ExperimentBuilder(self.driver, self.username)
        self.builder.new_experiment()
        self.builder.step_1(name="Phase test experiment")
        self.builder.complete_experiment()

        # Wait for roadmap page to load.
        FindElementBy.css_selector(self.driver, '.phase_container')

        self.roadmap_url = self.driver.current_url

    def tearDown(self):
        '''
        Removes all experiment created by this test.
        '''
        super(TestPhaseCreation, self).tearDown()
        self.driver.get(self.roadmap_url)
        self.builder.delete_experiment()

    def test_create_phases(self):
        '''
        Creates some phases.
        '''
        with open('drag_and_drop_helper.js') as f:
            self.driver.execute_script(f.read())

        def find_phases():
            return self.driver.find_elements_by_css_selector(
                '#phases .phase_element')

        def insert_phase(position, name):
            self.driver.execute_script(
                'var target = $( "#phases .phase_separator" )[{}];'.format(position) +
                '$( ".new_phase" ).simulateDragDrop({' +
                '   dropTarget: target' +
                '})')
            ActionChains(self.driver).send_keys(name, Keys.ENTER).perform()
            FindElementBy.xpath(self.driver,
                '//div[@id="phases"]/div[@class="phase_element" and contains(., "{}")]'.format(name))
            self.assertEquals(name, find_phases()[position].text)

        # Insert phase into existing roadmap.
        insert_phase(0, 'B')

        # Insert phase before existing phases.
        insert_phase(0, 'A')

        # Insert phase after existing phases.
        insert_phase(2, 'D')

        # Insert phase between existing phases.
        insert_phase(2, 'C')

        labels = ('A', 'B', 'C', 'D')

        # Check phase order.
        phases = find_phases()
        for i, label in enumerate(labels):
            self.assertEquals(label, phases[i].text)

        # Delete phase.
        button = phases[0].find_element_by_css_selector('.phase_delete_button')
        chain = ActionChains(self.driver).\
            move_to_element(phases[0]).\
            move_to_element(button).\
            click()
        TestUtils.do_and_confirm(self.driver, chain.perform)
        self.assertIn(
            'Phase deleted.',
            self.driver.find_element_by_css_selector('.flashes').text)
        self.assertEquals(3, len(find_phases()))
