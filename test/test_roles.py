from .base_test_case import BaseTestCase
from .experiment_builder import ExperimentBuilder
from .utils import TestUtils


class TestAdminPermissions(BaseTestCase):
    username = "emotiv_admin"
    def test_cannot_build_experiments(self):
        self.driver.get(self.emotiv_url + '/experiments/new')
        self.assert_in_flashes('cannot build')

    def test_cannot_take_experiments(self):
        fail_to_take_experiment(self)


class TestBuilderPermissions(BaseTestCase):
    username = "emotiv_builder"
    def test_cannot_modify_experiments_from_other_orgs(self):
        # Create an experiment.
        builder = ExperimentBuilder(self.driver, self.username)
        builder.new_experiment()
        builder.step_1('test experiment ' + TestUtils.generate_unique_key())
        exp_id = self.driver.current_url.rsplit('/', 1)[1]
        self.logout()

        # Log in with an account in a different org and try to edit.
        self.ensure_logged_in('emotiv_auto')
        self.driver.get(self.emotiv_url + '/experiments/edit/roadmap/{}'.format(exp_id))
        self.assert_in_flashes('do not have permission')

    def test_cannot_take_experiments(self):
        fail_to_take_experiment(self)


class TestViewerPermissions(BaseTestCase):
    username = "emotiv_auto"
    def test_cannot_take_private_experiments(self):
        name = 'test experiment ' + TestUtils.generate_unique_key()
        builder = ExperimentBuilder(self.driver, self.username)
        builder.new_experiment()
        builder.step_1(name)
        exp_id = self.driver.current_url.rsplit('/', 1)[1]
        builder.step_2()
        builder.step_3()
        builder.step_4()
        builder.step_5(private=True)
        builder.complete_experiment(submit=True, approve=True, test_case=self, name=name)

        self.ensure_logged_in('emotiv_viewer')
        self.driver.get(self.emotiv_url + '/experiments/detail/{}'.format(exp_id))
        self.assert_in_flashes('have not been invited')

            
def fail_to_take_experiment(test):
    # Create and submit experiment.
    name = 'test experiment ' + TestUtils.generate_unique_key()
    test.logout()
    test.ensure_logged_in('emotiv_auto')
    builder = ExperimentBuilder(test.driver, 'emotiv_auto')
    builder.new_experiment()
    builder.step_1(name)
    exp_id = test.driver.current_url.rsplit('/', 1)[1]
    builder.complete_experiment(submit=True, approve=True, test_case=test, name=name)

    # Try to take experiment.
    test.ensure_logged_in(test.username)
    test.driver.get(test.emotiv_url + '/experiments/detail/{}'.format(exp_id))
    test.assert_in_flashes('can not participate')
