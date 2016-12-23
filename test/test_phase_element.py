import time
from .base_test_case import BaseTestCase
from .experiment_builder import ExperimentBuilder
from .utils import TestUtils, FindElementBy
from selenium import webdriver

class PhaseElementTestCase(BaseTestCase):

    username = 'emotiv_auto'

    # The phase editor layout looks really funky in phantomjs
    driver_factory = webdriver.Chrome

    @classmethod
    def setUpClass(cls):
        '''
        '''
        super(PhaseElementTestCase, cls).setUpClass()
        cls.experiment = cls.__name__ + ' ' + TestUtils.generate_unique_key()

    def setUp(self):
        '''
        Called before every test
        '''
        super(PhaseElementTestCase, self).setUp()
        self.builder = ExperimentBuilder(self.driver, self.username)

        # Determine if we need to create it or re-use existing
        self.builder.search_for_experiment(self.experiment)
        experiments = self.builder.get_editable_experiments()
        if len(experiments) == 0:
            self.builder.create_basic_experiment(self.experiment)
        else:
            self.builder.browse_to_edit_experiment_roadmap(experiments[0])
            self.builder.complete_experiment()

    @classmethod
    def tearDownClass(cls):
        '''
        Removes all experiments created in this test case
        '''
        ExperimentBuilder(cls.driver, cls.username).delete_all_experiments(cls.experiment)
        super(PhaseElementTestCase, cls).tearDownClass()


class TestTextPhaseElement(PhaseElementTestCase):

    def test_create_text_phase_element_with_no_text(self):
        '''
        Verifies that a user cannot create a text phase element with no text
        '''
        self.builder.open_phase('Text Phase Element')
        self.builder.new_text_phase_element('')
        self.assert_in_flashes('Text or Question: This field is required')

    def test_create_text_phase_element_with_some_text(self):
        '''
        Verifies that a user can create a text element with lots of text
        '''
        self.builder.open_phase('Text Phase Element')
        self.builder.new_text_phase_element('This is a text element')
        FindElementBy.xpath(self.driver, '//*[contains(text(), "This is a text element")]')

    def test_create_text_phase_element_with_lots_of_text(self):
        '''
        Verifies that a user can create a text element with lots of text
        '''
        self.builder.open_phase('Text Phase Element')
        text = "The quick, brown fox jumps over a lazy dog. DJs flock by when MTV ax quiz prog. Junk MTV quiz graced by fox whelps. Bawds jog, flick quartz, vex nymphs. Waltz, bad nymph, for quick jigs vex! Fox nymphs grab quick-jived waltz. Brick quiz whangs jumpy veldt fox. Bright vixens jump; dozy fowl quack. Quick wafting zephyrs vex bold Jim. Quick zephyrs blow, vexing daft Jim. Sex-charged fop blew my junk TV quiz. How quickly daft jumping zebras vex. Two driven jocks help fax my big quiz. Quick, Baz, get my woven flax jodhpurs! Now fax quiz Jack! my brave ghossft"
        self.builder.new_text_phase_element(text)
        FindElementBy.xpath(self.driver, '//*[contains(text(), "{}")]'.format(text))


class TestQuestionNoText(PhaseElementTestCase):

    def test_single(self):
        '''
        Verifies a single select type cannot be empty
        '''
        self.builder.open_phase('Question Phase Element')
        self.builder.new_question_phase_element('', 'single')
        self.assert_in_flashes('Text or Question: This field is required')

    def test_multi(self):
        '''
        Verifies a multiple select type cannot be empty
        '''
        self.builder.open_phase('Question Phase Element')
        self.builder.new_question_phase_element('', 'multiple')
        self.assert_in_flashes('Text or Question: This field is required')

    def test_datetime(self):
        '''
        Verifies a datetime type cannot be empty
        '''
        self.builder.open_phase('Question Phase Element')
        self.builder.new_question_phase_element('', 'datetime')
        self.assert_in_flashes('Text or Question: This field is required')

    def test_open_text(self):
        '''
        Verifies an open text type cannot be empty
        '''
        self.builder.open_phase('Question Phase Element')
        self.builder.new_question_phase_element('', 'text')
        self.assert_in_flashes('Text or Question: This field is required')

    def test_numeric_value(self):
        '''
        Verifies a numeric value type cannot be empty
        '''
        self.builder.open_phase('Question Phase Element')
        self.builder.new_question_phase_element('', 'numeric')
        self.assert_in_flashes('Text or Question: This field is required')

    def test_all_combinations(self):
        '''
        Verifies any question type requires text

        Sleeps are required between selecting another type or selenium throws
        a stale element reference exception.
        '''
        self.builder.open_phase('Question Phase Element')

        self.builder.new_question_phase_element('', 'text')
        self.assert_in_flashes('Text or Question: This field is required')

        time.sleep(.25)

        self.builder.select_question_type('multiple')
        self.builder.submit_new_phase_element()
        self.assert_in_flashes('Text or Question: This field is required')

        time.sleep(.25)

        self.builder.select_question_type('single')
        self.builder.submit_new_phase_element()
        self.assert_in_flashes('Text or Question: This field is required')

        time.sleep(.25)

        self.builder.select_question_type('datetime')
        self.builder.submit_new_phase_element()
        self.assert_in_flashes('Text or Question: This field is required')

        time.sleep(.25)

        self.builder.select_question_type('numeric')
        self.builder.submit_new_phase_element()
        self.assert_in_flashes('Text or Question: This field is required')


class TestQuestionSingleSelect(PhaseElementTestCase):

    def setUp(self):
        super(TestQuestionSingleSelect, self).setUp()
        self.builder.open_phase('Single Select Question')

    def tearDown(self):
        super(TestQuestionSingleSelect, self).tearDown()
        self.builder.delete_phase(self)

    def test_no_answer(self):
        '''
        Verifies a single select question with no answer
        '''
        question = 'How are you feeling today?'
        self.builder.new_question_phase_element(question, 'single')
        self.builder.assert_question(self, 1, question)

    def test_large_question(self):
        '''
        Verifies a single select question with a large amount of text
        '''
        question = 'How does the quick brown fox jump over the lazy dog? How does the quick brown fox jump over the lazy dog?How does the quick brown fox jump over the lazy dog?How does the quick brown fox jump over the lazy dog?How does the quick brown fox jump over the lazy dog?How does the quick brown fox jump over the lazy dog?How does the quick brown fox jump over the lazy dog?How does the quick brown fox jump over the lazy dog?How does the quick brown fox jump over the lazy dog?How does the quick brown fox jump over the lazy dog?How does the quick brown fox jump over the lazy dog?'
        self.builder.new_question_phase_element(question, 'single')
        self.builder.assert_question(self, 1, question)

    def test_order_with_no_answers(self):
        '''
        Verifies order of single select questions entered
        '''
        self.builder.new_question_phase_element('One?', 'single')
        self.builder.assert_question(self, 1, 'One?')

        self.builder.new_question_phase_element('Two?', 'single')
        self.builder.assert_question(self, 2, 'Two?')

        self.builder.new_question_phase_element('Three?', 'single')
        self.builder.assert_question(self, 3, 'Three?')

        self.builder.new_question_phase_element('Four?', 'single')
        self.builder.assert_question(self, 4, 'Four?')

    def test_answer_with_no_text(self):
        '''
        Verifies that text is required in the answer dialog for single select
        '''
        self.builder.new_question_phase_element('One?', 'single')
        self.builder.assert_question(self, 1, 'One?')

        self.builder.add_answer_to_question(1, '')
        self.assert_in_flashes('value: This field is required')
        self.builder.close_question_answer_modal()

    def test_question_with_single_answer(self):
        '''
        Verifies a single select question with a single answer
        '''
        self.builder.new_question_phase_element('How are you feeling today?', 'single')
        self.builder.assert_question(self, 1, 'How are you feeling today?')

        self.builder.add_answer_to_question(1, 'Fine')
        self.builder.assert_answer_in_question(self, 1, 1, 'Fine')

    def test_question_with_multiple_answers(self):
        '''
        Verifies single select answer order on insert and delete
        '''
        self.builder.new_question_phase_element('How are you feeling today?', 'single')
        self.builder.assert_question(self, 1, 'How are you feeling today?')

        self.builder.add_answer_to_question(1, 'Terrible')
        self.builder.assert_answer_in_question(self, 1, 1, 'Terrible')

        self.builder.add_answer_to_question(1, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 1, 'Terrible')
        self.builder.assert_answer_in_question(self, 1, 2, 'Bad')

        self.builder.add_answer_to_question(1, 'So so')
        self.builder.assert_answer_in_question(self, 1, 1, 'Terrible')
        self.builder.assert_answer_in_question(self, 1, 2, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 3, 'So so')

        self.builder.add_answer_to_question(1, 'Good')
        self.builder.assert_answer_in_question(self, 1, 1, 'Terrible')
        self.builder.assert_answer_in_question(self, 1, 2, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 3, 'So so')
        self.builder.assert_answer_in_question(self, 1, 4, 'Good')

        self.builder.add_answer_to_question(1, 'Amazing')
        self.builder.assert_answer_in_question(self, 1, 1, 'Terrible')
        self.builder.assert_answer_in_question(self, 1, 2, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 3, 'So so')
        self.builder.assert_answer_in_question(self, 1, 4, 'Good')
        self.builder.assert_answer_in_question(self, 1, 5, 'Amazing')

        # Verify delete first answer
        self.builder.delete_answer_from_question(1, 1) # Delete terrible
        self.builder.assert_answer_in_question(self, 1, 1, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 2, 'So so')
        self.builder.assert_answer_in_question(self, 1, 3, 'Good')
        self.builder.assert_answer_in_question(self, 1, 4, 'Amazing')

        # Verify delete last answer
        self.builder.delete_answer_from_question(1, 4) # Delete Amazing
        self.builder.assert_answer_in_question(self, 1, 1, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 2, 'So so')
        self.builder.assert_answer_in_question(self, 1, 3, 'Good')

        # Verify delete last answer
        self.builder.delete_answer_from_question(1, 2) # Delete So so
        self.builder.assert_answer_in_question(self, 1, 1, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 2, 'Good')

        # Add one back
        self.builder.add_answer_to_question(1, 'Terrible')
        self.builder.assert_answer_in_question(self, 1, 1, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 2, 'Good')
        self.builder.assert_answer_in_question(self, 1, 3, 'Terrible')

    def test_multiple_question_with_multiple_answers(self):
        '''
        Verifies order of single select questions entered
        '''
        self.builder.new_question_phase_element('How are you feeling today?', 'single')
        self.builder.assert_question(self, 1, 'How are you feeling today?')

        self.builder.add_answer_to_question(1, 'Terrible')
        self.builder.assert_answer_in_question(self, 1, 1, 'Terrible')

        self.builder.add_answer_to_question(1, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 2, 'Bad')

        self.builder.add_answer_to_question(1, 'So so')
        self.builder.assert_answer_in_question(self, 1, 3, 'So so')

        self.builder.add_answer_to_question(1, 'Good')
        self.builder.assert_answer_in_question(self, 1, 4, 'Good')

        self.builder.add_answer_to_question(1, 'Amazing')
        self.builder.assert_answer_in_question(self, 1, 5, 'Amazing')

        self.builder.new_question_phase_element('What kind of car do you drive?', 'single')
        self.builder.assert_question(self, 2, 'What kind of car do you drive?')

        self.builder.add_answer_to_question(2, 'Ford')
        self.builder.assert_answer_in_question(self, 2, 1, 'Ford')

        self.builder.add_answer_to_question(2, 'GM')
        self.builder.assert_answer_in_question(self, 2, 2, 'GM')

        self.builder.add_answer_to_question(2, 'Toyota')
        self.builder.assert_answer_in_question(self, 2, 3, 'Toyota')

        self.builder.add_answer_to_question(2, 'Other')
        self.builder.assert_answer_in_question(self, 2, 4, 'Other')


class TestQuestionMultipleSelect(PhaseElementTestCase):

    def setUp(self):
        super(TestQuestionMultipleSelect, self).setUp()
        self.builder.open_phase('Multiple Select Question')

    def tearDown(self):
        super(TestQuestionMultipleSelect, self).tearDown()
        self.builder.delete_phase(self)

    def test_no_answer(self):
        '''
        Verifies a multiple select question with no answer
        '''
        question = 'How are you feeling today?'
        self.builder.new_question_phase_element(question, 'multiple')
        self.builder.assert_question(self, 1, question)

    def test_large_question(self):
        '''
        Verifies a multiple select question with a large amount of text
        '''
        question = 'How does the quick brown fox jump over the lazy dog? How does the quick brown fox jump over the lazy dog?How does the quick brown fox jump over the lazy dog?How does the quick brown fox jump over the lazy dog?How does the quick brown fox jump over the lazy dog?How does the quick brown fox jump over the lazy dog?How does the quick brown fox jump over the lazy dog?How does the quick brown fox jump over the lazy dog?How does the quick brown fox jump over the lazy dog?How does the quick brown fox jump over the lazy dog?How does the quick brown fox jump over the lazy dog?'
        self.builder.new_question_phase_element(question, 'multiple')
        self.builder.assert_question(self, 1, question)

    def test_order_with_no_answers(self):
        '''
        Verifies order of multiple select questions entered
        '''
        self.builder.new_question_phase_element('One?', 'multiple')
        self.builder.assert_question(self, 1, 'One?')

        self.builder.new_question_phase_element('Two?', 'multiple')
        self.builder.assert_question(self, 2, 'Two?')

        self.builder.new_question_phase_element('Three?', 'multiple')
        self.builder.assert_question(self, 3, 'Three?')

        self.builder.new_question_phase_element('Four?', 'multiple')
        self.builder.assert_question(self, 4, 'Four?')

    def test_answer_with_no_text(self):
        '''
        Verifies that text is required in the answer dialog for multiple select
        '''
        self.builder.new_question_phase_element('One?', 'multiple')
        self.builder.assert_question(self, 1, 'One?')

        self.builder.add_answer_to_question(1, '')
        self.assert_in_flashes('value: This field is required')
        self.builder.close_question_answer_modal()

    def test_question_with_single_answer(self):
        '''
        Verifies a multiple select question with a single answer
        '''
        self.builder.new_question_phase_element('How are you feeling today?', 'multiple')
        self.builder.assert_question(self, 1, 'How are you feeling today?')

        self.builder.add_answer_to_question(1, 'Fine')
        self.builder.assert_answer_in_question(self, 1, 1, 'Fine')

    def test_question_with_multiple_answers(self):
        '''
        Verifies multiple select answers and deletion
        '''
        self.builder.new_question_phase_element('How are you feeling today?', 'multiple')
        self.builder.assert_question(self, 1, 'How are you feeling today?')

        self.builder.add_answer_to_question(1, 'Terrible')
        self.builder.assert_answer_in_question(self, 1, 1, 'Terrible')

        self.builder.add_answer_to_question(1, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 1, 'Terrible')
        self.builder.assert_answer_in_question(self, 1, 2, 'Bad')

        self.builder.add_answer_to_question(1, 'So so')
        self.builder.assert_answer_in_question(self, 1, 1, 'Terrible')
        self.builder.assert_answer_in_question(self, 1, 2, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 3, 'So so')

        self.builder.add_answer_to_question(1, 'Good')
        self.builder.assert_answer_in_question(self, 1, 1, 'Terrible')
        self.builder.assert_answer_in_question(self, 1, 2, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 3, 'So so')
        self.builder.assert_answer_in_question(self, 1, 4, 'Good')

        self.builder.add_answer_to_question(1, 'Amazing')
        self.builder.assert_answer_in_question(self, 1, 1, 'Terrible')
        self.builder.assert_answer_in_question(self, 1, 2, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 3, 'So so')
        self.builder.assert_answer_in_question(self, 1, 4, 'Good')
        self.builder.assert_answer_in_question(self, 1, 5, 'Amazing')

        # Verify delete first answer
        self.builder.delete_answer_from_question(1, 1) # Delete terrible
        self.builder.assert_answer_in_question(self, 1, 1, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 2, 'So so')
        self.builder.assert_answer_in_question(self, 1, 3, 'Good')
        self.builder.assert_answer_in_question(self, 1, 4, 'Amazing')

        # Verify delete last answer
        self.builder.delete_answer_from_question(1, 4) # Delete Amazing
        self.builder.assert_answer_in_question(self, 1, 1, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 2, 'So so')
        self.builder.assert_answer_in_question(self, 1, 3, 'Good')

        # Verify delete last answer
        self.builder.delete_answer_from_question(1, 2) # Delete So so
        self.builder.assert_answer_in_question(self, 1, 1, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 2, 'Good')

        # Add one back
        self.builder.add_answer_to_question(1, 'Terrible')
        self.builder.assert_answer_in_question(self, 1, 1, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 2, 'Good')
        self.builder.assert_answer_in_question(self, 1, 3, 'Terrible')

    def test_multiple_question_with_multiple_answers(self):
        '''
        Verifies multiple select questions with multiple answers
        '''
        self.builder.new_question_phase_element('How are you feeling today?', 'multiple')
        self.builder.assert_question(self, 1, 'How are you feeling today?')
        self.builder.add_answer_to_question(1, 'Terrible')
        self.builder.assert_answer_in_question(self, 1, 1, 'Terrible')
        self.builder.add_answer_to_question(1, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 2, 'Bad')
        self.builder.add_answer_to_question(1, 'So so')
        self.builder.assert_answer_in_question(self, 1, 3, 'So so')
        self.builder.add_answer_to_question(1, 'Good')
        self.builder.assert_answer_in_question(self, 1, 4, 'Good')
        self.builder.add_answer_to_question(1, 'Amazing')
        self.builder.assert_answer_in_question(self, 1, 5, 'Amazing')

        self.builder.new_question_phase_element('What kind of car do you drive?', 'multiple')
        self.builder.assert_question(self, 2, 'What kind of car do you drive?')
        self.builder.add_answer_to_question(2, 'Ford')
        self.builder.assert_answer_in_question(self, 2, 1, 'Ford')
        self.builder.add_answer_to_question(2, 'GM')
        self.builder.assert_answer_in_question(self, 2, 2, 'GM')
        self.builder.add_answer_to_question(2, 'Toyota')
        self.builder.assert_answer_in_question(self, 2, 3, 'Toyota')
        self.builder.add_answer_to_question(2, 'Other')
        self.builder.assert_answer_in_question(self, 2, 4, 'Other')

        self.builder.new_question_phase_element('What kind of home do you live in?', 'single')
        self.builder.assert_question(self, 3, 'What kind of home do you live in?')
        self.builder.add_answer_to_question(3, 'House')
        self.builder.assert_answer_in_question(self, 3, 1, 'House')
        self.builder.add_answer_to_question(3, 'Apartment')
        self.builder.assert_answer_in_question(self, 3, 2, 'Apartment')
        self.builder.add_answer_to_question(3, 'Townhouse')
        self.builder.assert_answer_in_question(self, 3, 3, 'Townhouse')
        self.builder.add_answer_to_question(3, 'Condo')
        self.builder.assert_answer_in_question(self, 3, 4, 'Condo')

        self.builder.delete_question(2, 'multiple')

        self.builder.assert_question(self, 1, 'How are you feeling today?')
        self.builder.assert_answer_in_question(self, 1, 1, 'Terrible')
        self.builder.assert_answer_in_question(self, 1, 2, 'Bad')
        self.builder.assert_answer_in_question(self, 1, 3, 'So so')
        self.builder.assert_answer_in_question(self, 1, 4, 'Good')
        self.builder.assert_answer_in_question(self, 1, 5, 'Amazing')
        self.builder.assert_question(self, 2, 'What kind of home do you live in?')
        self.builder.assert_answer_in_question(self, 2, 1, 'House')
        self.builder.assert_answer_in_question(self, 2, 2, 'Apartment')
        self.builder.assert_answer_in_question(self, 2, 3, 'Townhouse')
        self.builder.assert_answer_in_question(self, 2, 4, 'Condo')


class TestQuestionDatetime(PhaseElementTestCase):

    def setUp(self):
        super(TestQuestionDatetime, self).setUp()
        self.builder.open_phase('Datetime Question')
        self.question_type = 'datetime'

    def tearDown(self):
        super(TestQuestionDatetime, self).tearDown()
        self.builder.delete_phase(self)

    def test_one_question(self):
        '''
        Verifies a datetime question and deleting
        '''
        question = 'When did you graduate high school?'
        self.builder.new_question_phase_element(question, self.question_type)
        self.builder.assert_question(self, 1, question)
        self.builder.delete_question(1, self.question_type)

    def test_one_question_lots_of_text(self):
        '''
        Verifies datetime question with lots of text.
        '''
        question = 'When did you graduate high school?When did you graduate high school?When did you graduate high school?When did you graduate high school?When did you graduate high school?When did you graduate high school?When did you graduate high school?When did you graduate high school?When did you graduate high school?'
        self.builder.new_question_phase_element(question, self.question_type)
        self.builder.assert_question(self, 1, question)

    def test_multiple_question(self):
        '''
        Verifies multiple datetime questions and deleting
        '''
        self.builder.new_question_phase_element('One?', self.question_type)
        self.builder.assert_question(self, 1, 'One?')

        self.builder.new_question_phase_element('Two?', self.question_type)
        self.builder.assert_question(self, 2, 'Two?')

        self.builder.new_question_phase_element('Three?', self.question_type)
        self.builder.assert_question(self, 3, 'Three?')

        self.builder.new_question_phase_element('Four?', self.question_type)
        self.builder.assert_question(self, 4, 'Four?')

        self.builder.delete_question(2, self.question_type)
        self.builder.assert_question(self, 1, 'One?')
        self.builder.assert_question(self, 2, 'Three?')
        self.builder.assert_question(self, 3, 'Four?')

        self.builder.delete_question(3, self.question_type)
        self.builder.assert_question(self, 1, 'One?')
        self.builder.assert_question(self, 2, 'Three?')

        self.builder.delete_question(1, self.question_type)
        self.builder.assert_question(self, 1, 'Three?')

        self.builder.delete_question(1, self.question_type)

        self.assertEqual('No elements added to phase yet.',
            FindElementBy.xpath(self.driver, '//div[@id="phase_content"]/div').text)


class TestQuestionOpenText(PhaseElementTestCase):

    def setUp(self):
        super(TestQuestionOpenText, self).setUp()
        self.builder.open_phase('Open Text Question')
        self.question_type = 'text'

    def tearDown(self):
        super(TestQuestionOpenText, self).tearDown()
        self.builder.delete_phase(self)

    def test_one_question(self):
        '''
        Verifies an open text question and deleting
        '''
        question = 'How do you feel about the political candidates?'
        self.builder.new_question_phase_element(question, self.question_type)
        self.builder.assert_question(self, 1, question)
        self.builder.delete_question(1, self.question_type)

    def test_one_question_lots_of_text(self):
        '''
        Verifies open text question with lots of text.
        '''
        question = 'How do you feel about the political candidates?How do you feel about the political candidates?How do you feel about the political candidates?How do you feel about the political candidates?How do you feel about the political candidates?How do you feel about the political candidates?How do you feel about the political candidates?How do you feel about the political candidates?How do you feel about the political candidates?How do you feel about the political candidates?How do you feel about the political candidates?'
        self.builder.new_question_phase_element(question, self.question_type)
        self.builder.assert_question(self, 1, question)

    def test_multiple_question(self):
        '''
        Verifies multiple open text questions and deleting
        '''
        self.builder.new_question_phase_element('One?', self.question_type)
        self.builder.assert_question(self, 1, 'One?')

        self.builder.new_question_phase_element('Two?', self.question_type)
        self.builder.assert_question(self, 2, 'Two?')

        self.builder.new_question_phase_element('Three?', self.question_type)
        self.builder.assert_question(self, 3, 'Three?')

        self.builder.new_question_phase_element('Four?', self.question_type)
        self.builder.assert_question(self, 4, 'Four?')

        self.builder.delete_question(2, self.question_type)
        self.builder.assert_question(self, 1, 'One?')
        self.builder.assert_question(self, 2, 'Three?')
        self.builder.assert_question(self, 3, 'Four?')

        self.builder.delete_question(3, self.question_type)
        self.builder.assert_question(self, 1, 'One?')
        self.builder.assert_question(self, 2, 'Three?')

        self.builder.delete_question(1, self.question_type)
        self.builder.assert_question(self, 1, 'Three?')

        self.builder.delete_question(1, self.question_type)

        self.assertEqual('No elements added to phase yet.',
            FindElementBy.xpath(self.driver, '//div[@id="phase_content"]/div').text)


class TestQuestionNumeric(PhaseElementTestCase):

    def setUp(self):
        super(TestQuestionNumeric, self).setUp()
        self.builder.open_phase('Numeric Question')
        self.question_type = 'numeric'

    def tearDown(self):
        super(TestQuestionNumeric, self).tearDown()
        self.builder.delete_phase(self)

    def test_one_question(self):
        '''
        Verifies numeric question and deleting
        '''
        question = 'How do you feel about the political candidates?'
        self.builder.new_question_phase_element(question, self.question_type)
        self.builder.assert_question(self, 1, question)
        self.builder.delete_question(1, self.question_type)

    def test_one_question_lots_of_text(self):
        '''
        Verifies numeric question with lots of text.
        '''
        question = 'How do you feel about the political candidates?How do you feel about the political candidates?How do you feel about the political candidates?How do you feel about the political candidates?How do you feel about the political candidates?How do you feel about the political candidates?How do you feel about the political candidates?How do you feel about the political candidates?How do you feel about the political candidates?How do you feel about the political candidates?How do you feel about the political candidates?'
        self.builder.new_question_phase_element(question, self.question_type)
        self.builder.assert_question(self, 1, question)

    def test_multiple_question(self):
        '''
        Verifies multiple numeric questions and deleting
        '''
        self.builder.new_question_phase_element('One?', self.question_type)
        self.builder.assert_question(self, 1, 'One?')

        self.builder.new_question_phase_element('Two?', self.question_type)
        self.builder.assert_question(self, 2, 'Two?')

        self.builder.new_question_phase_element('Three?', self.question_type)
        self.builder.assert_question(self, 3, 'Three?')

        self.builder.new_question_phase_element('Four?', self.question_type)
        self.builder.assert_question(self, 4, 'Four?')

        self.builder.delete_question(2, self.question_type)
        self.builder.assert_question(self, 1, 'One?')
        self.builder.assert_question(self, 2, 'Three?')
        self.builder.assert_question(self, 3, 'Four?')

        self.builder.delete_question(3, self.question_type)
        self.builder.assert_question(self, 1, 'One?')
        self.builder.assert_question(self, 2, 'Three?')

        self.builder.delete_question(1, self.question_type)
        self.builder.assert_question(self, 1, 'Three?')

        self.builder.delete_question(1, self.question_type)

        self.assertEqual('No elements added to phase yet.',
            FindElementBy.xpath(self.driver, '//div[@id="phase_content"]/div').text)
