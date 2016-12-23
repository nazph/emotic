import unittest

from selenium.webdriver.common.action_chains import ActionChains

from .base_test_case import BaseTestCase

class TestViewer(BaseTestCase):

    username = "emotiv_viewer"

    def test_view_experiments(self):
        '''
        Test view all experiments
        '''
        self.assertIn('current experiments', self.driver.page_source)
        self.assertIn('Experiments', self.driver.page_source)
        self.assertIn('View', self.driver.page_source)
        self.assertEqual(self.driver.current_url, self.emotiv_url + '/experiments/')

    @unittest.skip('needs work')
    def test_paginate_experiments(self):
        '''
        Test paginate experiments. Click 2 and not see experiment on page 1. Click 2 and see experiment
        '''
        link = self.driver.find_elements_by_xpath('//a[@class="experiment_box_modal_button"]')[0].get_attribute('href')
        link = ("/").join(link.split("/")[3:])
        self.assertIn(link, self.driver.page_source)
        self.driver.find_element_by_partial_link_text('2').click()
        self.assertEqual(self.driver.current_url, self.emotiv_url +"/experiments/sort_by/name/2")
        self.assertNotIn('Auto Experiment', self.driver.page_source)
        self.assertNotIn(link, self.driver.page_source)
        self.driver.find_element_by_partial_link_text('1').click()
        self.assertEqual(self.driver.current_url, self.emotiv_url +"/experiments/sort_by/name/1")
        self.assertIn(link, self.driver.page_source)

    def test_search_experiments(self):
        '''
        Test search experiments.
        '''
        self.driver.find_element_by_name('search').send_keys('Auto Experiment')
        self.driver.find_element_by_name('submit').click()
        link = self.driver.find_elements_by_xpath('//a[@class="experiment_box_modal_button"]')[0].get_attribute('href')
        link = ("/").join(link.split("/")[3:])
        self.assertIn('Auto Experiment', self.driver.page_source)
        self.assertIn('1 current experiments', self.driver.page_source)

    def test_sort_experiments(self):
        '''
        Test sort experiments.
        '''
        # Click date
        element = self.driver.find_element_by_class_name("drop_btn")
        ActionChains(self.driver).move_to_element(element).click().perform()
        self.driver.find_element_by_link_text("Date").click()
        self.assertEqual(self.driver.current_url, self.emotiv_url + "/experiments/sort_by/date/1")
        count = self.driver.find_elements_by_css_selector('.experiment_box')
        self.assertEqual(8,len(count))
        self.assertNotIn('Auto Experiment', self.driver.page_source)

