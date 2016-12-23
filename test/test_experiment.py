from datetime import datetime, timedelta
from .base_test_case import BaseTestCase
from .experiment_builder import ExperimentBuilder
from .utils import TestUtils


class TestExperiment(BaseTestCase):

    def setUp(self):
        '''
        Called before every test
        '''
        super(TestExperiment, self).setUp()
        self.today = TestUtils.get_todays_date()
        self.tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        self.builder = ExperimentBuilder(self.driver, self.username)

    @classmethod
    def tearDownClass(cls):
        '''
        Removes all experiments created in this test case
        '''
        ExperimentBuilder(cls.driver, cls.username).delete_all_experiments()
        super(TestExperiment, cls).tearDownClass()

    #
    # --- Assertions ---
    #
    def assert_roadmap_screen(self):
        '''
        Asserts that we are on the Roadmap screen
        '''
        self.assertIn(
            'roadmap', self.driver.current_url,
            msg='Expected to be on the roadmap screen. current_url=%s' % (
                self.driver.current_url))

    #
    # ---  TESTS ---
    #
    def test_create_experiment(self):
        '''
        Verifies an experiment with today's date
        '''
        self.builder.new_experiment()
        self.builder.step_1()
        self.builder.step_2()
        self.builder.step_3()
        self.builder.step_4()
        self.builder.step_5()
        self.builder.step_6(10, self.today)
        self.assert_roadmap_screen()

    def test_create_experiment_with_image(self):
        '''
        Verifies an experiment with an image
        '''
        self.builder.new_experiment()
        self.builder.step_1()
        self.builder.step_2()
        self.builder.step_3()
        self.builder.step_4()
        self.builder.step_5(set_image=True, test_case=self)
        self.builder.step_6(10, self.tomorrow)
        self.assert_roadmap_screen()

    def test_create_experiment_with_recordings_permutations(self):
        '''
        Verifies an experiment recording permutations
        '''
        self.builder.new_experiment()
        self.builder.step_1()
        self.builder.step_2()
        self.builder.step_3()
        self.builder.step_4()
        self.builder.step_5()

        self.builder.step_6()
        self.assert_in_flashes('Number to collect:')
        self.assert_in_flashes('Start Date:')
        self.assert_in_flashes('End Date:')

        self.builder.step_6(10)
        self.assert_in_flashes('Start Date:')

        self.builder.step_6(-1, self.tomorrow)
        self.assert_in_flashes('Number to collect: Number must be between 0 and 1000000000')

        self.builder.step_6(-100000000000, self.tomorrow)
        self.assert_in_flashes('Number to collect: Number must be between 0 and 1000000000')

        self.builder.step_6(1000000001, self.tomorrow)
        self.assert_in_flashes('Number to collect: Number must be between 0 and 1000000000')

        self.builder.step_6(100000000, self.tomorrow)
        self.assert_roadmap_screen()

    def test_create_experiment_with_start_before_current_date(self):
        '''
        Verifies an experiment with start date before current date
        '''
        self.builder.new_experiment()
        self.builder.step_1()
        self.builder.step_2()
        self.builder.step_3()
        self.builder.step_4()
        self.builder.step_5()

        one_day_ago = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        self.builder.step_6(10, start_date=one_day_ago)

        self.assert_in_flashes('Start Date: Experiment cannot start in the past.', msg='Experiment cannot start in the past.')

    def test_create_experiment_with_start_after_end(self):
        '''
        Verifies an experiment with start date after end date
        '''
        self.builder.new_experiment()
        self.builder.step_1()
        self.builder.step_2()
        self.builder.step_3()
        self.builder.step_4()
        self.builder.step_5()

        two_days_from_now = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        one_day_from_now = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        self.builder.step_6(recordings=None, start_date=two_days_from_now, end_date=one_day_from_now)

        self.assert_in_flashes('End Date: Experiment cannot end before it has started', msg='Experiment cannot end before it has started')

    def test_create_experiment_with_eye_tracking_data(self):
        '''
        Verifies an experiment with eye tracking data
        '''
        self.builder.new_experiment()
        self.builder.step_1()
        self.builder.step_2()
        self.builder.step_3()
        self.builder.step_4()
        self.builder.step_5()
        self.builder.step_6(10, start_date=self.tomorrow, eye_tracking_data=True)
        self.assert_roadmap_screen()

    def test_create_experiment_with_web_tracking_data(self):
        '''
        Verifies an experiment with web tracking data
        '''
        self.builder.new_experiment()
        self.builder.step_1()
        self.builder.step_2()
        self.builder.step_3()
        self.builder.step_4()
        self.builder.step_5()
        self.builder.step_6(10, start_date=self.tomorrow, web_tracking_data=True)
        self.assert_roadmap_screen()

    def test_submit_empty_experiment(self):
        '''
        Verifies submitting an experiment with no phases
        '''
        self.builder.new_experiment()
        self.builder.step_1(name="Empty Experiment")
        self.builder.complete_experiment()
        self.builder.submit_experiment()
        self.assert_in_flashes("Can't submit")

    def test_delete_experiment(self):
        '''
        Verifies deleting an experiment
        '''
        self.builder.new_experiment()
        self.builder.step_1(name="Experiment to delete")
        self.builder.complete_experiment()
        roadmap = self.driver.current_url
        self.builder.delete_experiment()
        self.assertEqual(self.driver.current_url, self.emotiv_url + '/experiments/')
        self.driver.get(roadmap)
        self.assertIn('404', self.driver.find_element_by_class_name('page-header').text)
