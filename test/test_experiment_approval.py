from .base_test_case import BaseTestCase
from .utils import TestUtils
from .experiment_builder import ExperimentBuilder

class TestExperimentApproval(BaseTestCase):

    username = "emotiv_builder"

    def setUp(self):
        '''
        Called before every test
        '''
        super(TestExperimentApproval, self).setUp()
        self.todays_date = TestUtils.get_todays_date()
        self.builder = ExperimentBuilder(self.driver, self.username)
        self.experiment_name = 'Experiment Approval ' + TestUtils.generate_unique_key()
        print(self.experiment_name)

    def tearDown(self):
        '''
        Called after every test
        '''
        super(TestExperimentApproval, self).tearDown()
        if self.experiment_name:
            self.builder.delete_all_experiments(name=self.experiment_name)

    def test_approve_experiment(self):
        '''
        Test verify approving experiments
        '''
        self.builder.create_basic_experiment(self.experiment_name, submit=True)
        self.logout()

        self.login("emotiv_admin")
        self.assertIn('Administration', self.driver.page_source)
        self.builder.approve_experiment(self.experiment_name)
        self.assertIn("Experiment request approved.",self.driver.page_source)
        self.assertNotIn(self.experiment_name,self.driver.page_source)
        self.logout()

        self.login("emotiv_builder")
        self.assertIn(self.builder.get_experiment_state(self.experiment_name),
            ['SCHEDULED','ONGOING'])


    def test_deny_experiment(self):
        '''
        Test verify deny experiments
        '''
        self.builder.create_basic_experiment(self.experiment_name, submit=True)
        self.logout()

        self.login("emotiv_admin")
        self.assertIn('Administration', self.driver.page_source)
        self.builder.deny_experiment(self.experiment_name)
        self.assertIn("Experiment request denied.",self.driver.page_source)
        self.assertNotIn(self.experiment_name,self.driver.page_source)
        self.logout()

        self.login("emotiv_builder")
        self.assertIn(self.builder.get_experiment_state(self.experiment_name),
            ['EDITING'])

    def test_deny_experiment_with_reason(self):
        '''
        Test deny experiments with reason
        '''
        self.builder.create_basic_experiment(self.experiment_name, submit=True)
        self.logout()
        self.login("emotiv_admin")
        self.assertIn('Administration', self.driver.page_source)
        self.builder.deny_experiment(self.experiment_name, "It has been denied")
        self.assertIn("Experiment request denied.",self.driver.page_source)
        self.assertNotIn(self.experiment_name,self.driver.page_source)
        self.logout()

        self.login("emotiv_builder")
        self.assertIn(self.builder.get_experiment_state(self.experiment_name),
            ['EDITING'])
