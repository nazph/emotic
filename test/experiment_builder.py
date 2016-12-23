import re

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.support.ui import Select
from .base_test_case import BaseTestCase
from .utils import TestUtils, FindElementBy, FindElementsBy, wait_until_element_deleted

class ExperimentBuilder(object):
    '''
    Helper class to build experiments
    '''

    def __init__(self, driver, username):
        self.driver = driver
        self.username = username
        self.emotiv_url = BaseTestCase.emotiv_url
        self.todays_date = TestUtils.get_todays_date()

    def new_experiment(self):
        '''
        Clicks the New Experiment box
        '''
        element = self.driver.find_element_by_class_name('new_experiment_box')
        ActionChains(self.driver).move_to_element(element).click().perform()

    def delete_experiment(self):
        '''
        Delete the experiment. Requires to be on the Roadmap screen.
        '''
        TestUtils.do_and_confirm(
            self.driver,
            lambda: self.driver.find_element_by_xpath('//button[contains(text(), "Delete Experiment")]').click())

    def submit_experiment(self):
        '''
        Submit the experiment. Requires to be on the Roadmap screen.
        '''
        self.driver.find_element_by_xpath('//button[contains(text(), "Submit Experiment")]').click()

    def complete_experiment(self, submit=False, approve=False, test_case=None, name=''):
        '''
        Completes an experiment and ensures we are on the roadmap screen.

        Must start on the roadmap screen or a partially completed experiment.
        '''
        if 'step_' in self.driver.current_url:
            step = int(self.driver.current_url.split('/')[-2][-1])
        else:
            step = 7
        if step <= 2:
            self.step_2()
        if step <= 3:
            self.step_3()
        if step <= 4:
            self.step_4()
        if step <= 5:
            self.step_5()
        if step <= 6:
            self.step_6(10, start_date=TestUtils.get_date_from_today(days=3))

        if not submit:
            return

        self.create_basic_phase()
        self.submit_experiment()

        if not approve:
            return

        test_case.logout()
        test_case.ensure_logged_in('emotiv_admin')
        self.approve_experiment(name)
        test_case.logout()

    def view_experiment(self, name):
        '''
        Views the given experiment

        Assumes you are logged in as a viewer
        '''
        self.search_for_experiment(name)
        view = FindElementsBy.xpath(
                self.driver, '//a[@class="experiment_box_modal_button"]')
        # Hack around the fact that we can't trigger :hover in selenium:
        self.driver.get(view[0].get_attribute('href'))

    def get_experiment_state(self, name):
        self.search_for_experiment(name)
        experiments = FindElementsBy.class_name(self.driver, 'experiment_box', timeout=3)
        for experiment in experiments:
            ele = experiment.find_element_by_class_name('experiment_status')
            # Skip the "Create New Experiment" box
            if ele.text == '':
                continue
            return ele.text

    def search_for_experiment(self, name):
        '''
        Searches for experiments by name
        '''
        search_field = FindElementBy.xpath(self.driver, '//input[@name="search"]')
        search_field.clear()
        search_field.send_keys(name)
        FindElementBy.xpath(self.driver, '//input[@name="submit"]').click()

    def create_basic_experiment(self, name, submit=False):
        '''
        Creates a new experiment with basic options
        '''
        self.new_experiment()
        self.step_1(name=name)
        self.complete_experiment()
        self.create_basic_phase()
        if submit:
            self.submit_experiment()

    def create_basic_phase(self):
        # This needs to be done in Chrome, since PhantomJS
        # does not support the flexbox layout in the
        # experiment roadmap page.
        prev_driver = self.driver
        current_url = self.driver.current_url
        self.driver = webdriver.Chrome()
        self.driver.set_window_size(1440, 900)
        self.driver.implicitly_wait(5) # seconds
        TestUtils.ensure_logged_in(
            self.driver,
            self.username,
            BaseTestCase.emotiv_url,
            BaseTestCase.default_password)
        self.driver.get(current_url)

        # Insert the phase.
        self.insert_phase('p').click()
        self.new_text_phase_element('text')
        self.save_phase(None)

        # Revert to previous browser.
        self.driver.quit()
        self.driver = prev_driver

    def get_editable_experiments(self):
        '''
        Returns a list of experiments that are editable
        '''
        return re.findall('/experiments/edit/roadmap/([0-9]+)', self.driver.page_source)

    def browse_to_edit_experiment_roadmap(self, experiment):
        '''
        Simulates clicking on the edit experiment roadmap which will take the browser
        to the last unfinished step or the roadmap screen.
        '''
        self.driver.get(self.emotiv_url + '/experiments/edit/roadmap/' + str(experiment))

    def delete_all_experiments(self, name=None):
        '''
        Completes all unfinished experiments and deletes them
        '''
        self.driver.get(self.emotiv_url)
        while True:
            if name is not None:
                self.search_for_experiment(name)
            experiments = self.get_editable_experiments()
            if len(experiments) == 0:
                return
            self.browse_to_edit_experiment_roadmap(experiments[0])
            self.complete_experiment()
            self.delete_experiment()

    def add_attribute(self, attribute):
        '''
        Selects an attribute from the "Add Additional Criteria" dropdown.
        '''
        # Hover over the logo at the end to make the "Add Additional Criteria"
        # dropdown disappear.
        logo = self.driver.find_element_by_css_selector('.logo')

        attributes_dropdown = self.driver.find_element_by_xpath('//button[contains(., "Add Additional Criteria")]')
        ActionChains(self.driver). \
            move_to_element(attributes_dropdown). \
            move_to_element(self.driver.find_element_by_xpath('//li[contains(., "{}")]'.format(attribute))). \
            click(). \
            move_to_element(logo). \
            perform()

    def step_1(self, name=None, description=None):
        '''
        Experiment name and description
        '''
        if name is None:
            name = 'Experiment ' + TestUtils.generate_unique_key()
        self.driver.find_element_by_name('name').clear()
        self.driver.find_element_by_name('name').send_keys(name)
        if description is not None:
            self.driver.find_element_by_css_selector('textarea[name="description"]').clear()
            self.driver.find_element_by_css_selector('textarea[name="description"]').send_keys(description)
        self.driver.find_element_by_name('submit').click()

    def step_2(self):
        '''
        Chooses a template
        '''
        self.driver.find_element_by_xpath('//button[contains(., "No thanks")]').click()

    def step_3(self, suggestion='', unselect=[]):
        '''
        Elimination Criteria
        '''
        if len(suggestion) > 0:
            FindElementBy.xpath(self.driver, '//button[contains(., "request new criteria")]').click()
            el = FindElementBy.xpath(self.driver, '//textarea[@name="criteria_suggestion"]')
            el.clear()
            el.send_keys(suggestion)
        for attribute, option in unselect:
            self.add_attribute(attribute)
            # Attribute label
            el = FindElementBy.xpath(self.driver, '//label[contains(., "{}")]'.format(attribute))
            # Attribute box
            el = el.find_element_by_xpath('ancestor::div[contains(@class, "criteria_box")]')
            # Option
            el = el.find_element_by_xpath('descendant::label[contains(., "{}")]'.format(option))
            el.click()
        self.driver.find_element_by_name('submit').click()

    def step_4(self, attributes=['Gender','Date Of Birth', 'Location']):
        '''
        Information to collect
        '''
        for attribute in attributes:
            self.add_attribute(attribute)
        self.driver.find_element_by_name('submit').click()

    def step_5(self, set_image=False, test_case=None, private=False):
        '''
        Additional Information to collect
        '''
        if set_image:
            self.driver.find_element_by_xpath('//button[contains(., "Choose a previously uploaded image")]').click()
            self.driver.find_elements_by_css_selector('#prev-imgs .image_card')[0].click()
            test_case.assertEqual(len(self.driver.find_elements_by_css_selector('.image_card')), 1)
        if private:
            self.driver.find_element_by_xpath('//label[contains(., "Make experiment private")]').click()
        self.driver.find_element_by_name('submit').click()

    def step_6(self, recordings=None, start_date=None, end_date=None,
        eye_tracking_data=False, web_tracking_data=False, submit=True):
        '''
        Recording Details
        '''
        if eye_tracking_data:
            TestUtils.select_checkbox_with_text(self.driver, 'Check this box to collect eye-tracking data')

        if web_tracking_data:
            TestUtils.select_checkbox_with_text(self.driver, 'Check this box to collect web-tracking data')

        if recordings is not None:
            self.driver.find_element_by_name('recordings_collected').clear()
            self.driver.find_element_by_name('recordings_collected').send_keys(recordings)

        if start_date is not None:
            self.driver.find_element_by_name('start_date').clear()
            self.driver.find_element_by_name('start_date').send_keys(start_date)

        if end_date is not None:
            self.driver.find_element_by_name('end_date').clear()
            self.driver.find_element_by_name('end_date').send_keys(end_date)

        if submit:
            self.driver.find_element_by_name('submit').click()

    def prep_drag_and_drop(self):
        '''
        Loads the drag and drop helper script for the current page
        '''
        with open('drag_and_drop_helper.js') as f:
            self.driver.execute_script(f.read())

    def insert_phase(self, name, position=0):
        '''
        Inserts a new phase at the given position
        '''
        self.prep_drag_and_drop()
        self.driver.execute_script(
            'var target = $( "#phases .phase_separator" )[{}];'.format(position) +
            '$( ".new_phase" ).simulateDragDrop({' +
            '   dropTarget: target' +
            '})')
        ActionChains(self.driver).send_keys(name, Keys.ENTER).perform()
        return self.find_phase(name)

    def find_phase(self, name):
        '''
        Finds an existing phase
        '''
        return FindElementBy.xpath(self.driver,
            '//div[@id="phases"]/div[@class="phase_element" and contains(., "{}")]'.format(name),
            timeout=2)

    def find_phases(self):
        '''
        Finds all the current phases
        '''
        return FindElementsBy.css_selector(self.driver, '#phases .phase_element')

    def open_phase(self, name):
        '''
        Opens a phase with the given name
        '''
        try:
            phase = self.find_phase(name)
        except (NoSuchElementException, TimeoutException):
            phase = self.insert_phase(name)
        phase.click()

    def delete_phase(self, test_case):
        '''
        Deletes the phase that is currently open
        '''
        TestUtils.do_and_confirm(
            self.driver,
            lambda: FindElementBy.xpath(self.driver, '//button[contains(., "Delete")]').click())
        test_case.assert_in_flashes('Phase deleted')

    def save_phase(self, test_case):
        '''
        Saves the phase that is currently open
        '''
        FindElementBy.xpath(self.driver, '//button[contains(., "Save Phase Changes")]').click()
        if test_case is not None:
            test_case.assert_in_flashes('Updated phase')

    def new_phase_element(self):
        '''
        Clicks on the New button in the Phase Editor to open the Phase Editor modal.
        '''
        FindElementBy.xpath(self.driver, '//div[contains(text(), "New")]').click()

    def select_phase_element_type(self, element_type):
        '''
        Selects the phase element type that is passed in
        '''
        element_types = ['Text', 'Video', 'Image', 'Audio', 'Question']
        elements = self.driver.find_elements_by_css_selector('.element_type_selector')
        elements[element_types.index(element_type)].click()

    def submit_new_phase_element(self):
        '''
        Submits the new phase element to add it to the phase
        '''
        FindElementBy.xpath(self.driver, '//button[contains(text(), "SUBMIT")]').click()

    def new_text_phase_element(self, text):
        '''
        Creates a new Text phase element
        '''
        self.new_phase_element()
        self.select_phase_element_type('Text')

        text_input = FindElementBy.xpath(self.driver, '//textarea[@name="text"]')
        text_input.clear()
        text_input.send_keys(text)

        self.submit_new_phase_element()

    def set_question_field(self, question):
        '''
        Sets the question field for the question type of phase element.

        Expects:
        1. New Phase Element modal to be displayed
        2. Phase Element Type of Question to be selected
        '''
        question_input = FindElementBy.xpath(self.driver, '//input[@name="text"]')
        question_input.clear()
        question_input.send_keys(question)

    def add_answer_to_question(self, question_position, answer):
        '''
        Clicks the "Add New Answer" dialog for the question at the position (starts at 1)

        Expects:
        1. Phase Editor Screen
        2. The question at position X to exist
        '''
        self.get_phase_element(question_position).click()
        FindElementBy.xpath(self.driver, '//button[contains(text(), "Add additional row")]').click()
        self.set_question_answer_field(answer)
        self.submit_question_answer()

    def get_phase_element(self, n):
        '''
        Returns the n'th phase element card.
        '''
        return FindElementBy.xpath(self.driver,
            '//div[@id="element_cards"]/div[{}]'.format(n), timeout=3)

    def assert_question(self, test_case, question_position, question):
        '''
        Asserts that a question is in the correct position in the phase editor
        '''
        test_case.assertIn(
            question, self.get_phase_element(question_position).text)

    def assert_answer_in_question(self, test_case, question_position, answer_position, answer, allow_retry=True):
        '''
        Asserts that a question contains an answer at the correct position
        '''
        try:
            self.get_phase_element(question_position).click()
            answer_text = self.driver.find_elements_by_css_selector(
                '.element_question_answer_value')[answer_position-1].text
            test_case.assertEqual(answer_text, answer)
        except StaleElementReferenceException:
            if allow_retry:
                self.assert_answer_in_question(
                    test_case, question_position, answer_position, answer, False)
            else:
                raise

    def set_question_answer_field(self, answer):
        '''
        Sets the answer field for the new question answer dialog

        Expects:
        1. New Question Answer modal to be displayed
        '''
        element = FindElementBy.xpath(self.driver, '//input[@name="value"]')
        element.clear()
        element.send_keys(answer)

    def submit_question_answer(self):
        '''
        Submits a new question answer

        Expects:
        1. New Question Answer modal to be displayed
        '''
        FindElementBy.xpath(self.driver, '//form[@id="element_answer_form"]/div/button').click()

    def delete_answer_from_question(self, question_position, answer_position):
        '''
        Deletes an answer from a question
        '''
        self.get_phase_element(question_position).click()
        delete_button = self.driver.find_elements_by_css_selector(
            '.element_question_answer_delete span')[answer_position-1]
        delete_button.click()
        wait_until_element_deleted(self.driver, delete_button)

    def close_question_answer_modal(self):
        '''
        Closes a new question answer modal
        '''
        try:
            FindElementBy.xpath(self.driver,
                '//div[@class="element_answer_dialog_modal"]/div/div/button', timeout=3).click()
        except TimeoutException:
            pass

    def select_question_type(self, question_type):
        '''
        Selects the question type in the drop down list

        Expects:
        1. New Phase Element modal to be displayed
        2. Phase Element Type of Question to be selected
        '''
        lookup = {
            'single': 'ss',
            'multiple': 'ms',
            'datetime': 'dt',
            'text': 'ot',
            'numeric': 'nv'
        }
        if question_type not in lookup:
            raise Exception('Invalid question_type. Must be one of {}'.format(lookup.keys()))

        question_type_select = Select(FindElementBy.xpath(self.driver, '//select[@id="input_type"]'))
        question_type_select.select_by_value(lookup[question_type])

    def delete_question(self, question_position, question_type):
        '''
        Deletes a question from a phase
        '''
        self.driver.execute_script('test_hook_enable_hovers()')
        phase_element = self.get_phase_element(question_position)
        ActionChains(self.driver).\
            move_to_element(phase_element).\
            move_by_offset(15, 15).\
            move_to_element(phase_element.find_element_by_xpath('.//button')).\
            click().\
            perform()
        wait_until_element_deleted(self.driver, phase_element)

    def new_question_phase_element(self, question, question_type):
        '''
        Creates a new Question Phase Element

        Expects:
        1. Roadmap screen of an experiment
        '''
        self.new_phase_element()
        self.select_phase_element_type('Question')

        self.set_question_field(question)
        self.select_question_type(question_type)

        self.submit_new_phase_element()

    def approve_experiment(self, experiment):
        '''
        Approves an experiment
        '''
        # A React function handles this click. Wait until it is loaded before clicking.
        FindElementBy.css_selector(self.driver, '#react_loaded')
        experiment_link = FindElementBy.xpath(self.driver,
            '//a[contains(text(), "{0}")]'.format(experiment))
        experiment_link.find_element_by_xpath('following-sibling::button[contains(., "Approve")]').click()
        FindElementBy.xpath(self.driver, '//button[@type="submit"]').click()

    def deny_experiment(self, experiment, reason=''):
        '''
        Denies an experiment
        '''
        # A React function handles this click. Wait until it is loaded before clicking.
        FindElementBy.css_selector(self.driver, '#react_loaded')
        experiment_link = FindElementBy.xpath(self.driver,
            '//a[contains(text(), "{0}")]'.format(experiment))
        experiment_link.find_element_by_xpath('following-sibling::button[contains(., "Deny")]').click()
        FindElementBy.css_selector(self.driver, 'textarea').send_keys(reason)
        FindElementBy.xpath(self.driver, '//button[@type="submit"]').click()
