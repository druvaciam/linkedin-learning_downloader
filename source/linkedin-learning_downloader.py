# -*- coding: utf-8 -*-
"""
Created on Sun Oct 27 21:11:25 2019

@author: Aleh
"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
#from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import sys
import os
import time
from urllib.request import urlretrieve
import codecs
import argparse

timeout_sec = 8

def save_html(html, file_path):
    with codecs.open(file_path, "w", "utf-8") as file_object:
        file_object.write(html)

def wait_for_js(driver):
    wait = WebDriverWait(driver, timeout_sec)
    try:
        wait.until(lambda driver: driver.execute_script('return jQuery.active') == 0)
        print("jQuery.active == 0")
    except:
        pass
    try:
        wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        print("document.readyState == complete")
    except:
        pass

parser = argparse.ArgumentParser()
parser.add_argument('-email', '-login', help="user's linkedin login (email)")
parser.add_argument('-password', '-p', help="user's linkedin password")
parser.add_argument('-dir', '-folder', '-directory', help="directory to store content")
parser.add_argument('-driver', '-geckodriver', help="full geckodriver.exe path")
parser.add_argument('--courses', nargs='+', help="linkedin-learning courses' links to download")

args = parser.parse_args()
print(args)


autoplay_postfix = "?autoplay=true"
login_link = 'https://www.linkedin.com/uas/login?fromSignIn=true&trk=learning&_l=en_US&uno_session_redirect=https%3A%2F%2Fwww.linkedin.com%2Flearning%2F%3Ftrk%3Ddefault_guest_learning&session_redirect=%2Flearning%2FloginRedirect.html&is_enterprise_authed='

user_email = args.email
user_password = args.password

base_dir = args.dir.rstrip('/') # 'g:/usiakaje/linkedin-learning/'
geckodriver_path = args.driver # r'g:\prohi\geckodriver.exe'

courses = args.courses # ['https://www.linkedin.com/learning/c-plus-plus-design-patterns-creational']
print("courses:", courses)


driver = webdriver.Firefox(executable_path = geckodriver_path)
driver.set_page_load_timeout(50)
driver.maximize_window()

#driver.get("https://www.linkedin.com/learning/login?redirect=https%3A%2F%2Fwww.linkedin.com%2Flearning%2F%3Ftrk%3Ddefault_guest_learning&trk=sign_in")
driver.get(login_link)
wait_for_js(driver)

try:
    wait = WebDriverWait(driver, timeout_sec)
    wait.until(EC.element_to_be_clickable((By.ID, 'username')))
except:
    print(sys.exc_info()[0])

input_name = driver.find_element_by_id('username')
input_name.send_keys(user_email)
input_password = driver.find_element_by_id('password')
input_password.send_keys(user_password)
input_password.send_keys(Keys.RETURN)
wait_for_js(driver)

time.sleep(timeout_sec)

for course_url in courses:
    try:
        driver.get(course_url)
        wait_for_js(driver)
        time.sleep(timeout_sec)

        save_dir = f"{base_dir}/{course_url.split('/')[-1]}"
        exersice_dir = f"{save_dir}/Exercice Files"
        if not os.path.exists(exersice_dir):
            os.makedirs(exersice_dir)

        save_html(driver.page_source, f"{save_dir}/info.html")

        tabs = driver.find_elements_by_tag_name('artdeco-tab')
        for tab in tabs:
            if 'Exercise Files' in tab.get_attribute('innerHTML'):
                tab.click()
                time.sleep(timeout_sec)
                break

        elemets_a = driver.find_elements_by_tag_name('a')
        vid_refs = []
        exercise_refs = []
        for a in elemets_a:
            href = a.get_attribute('href')
            if course_url in href and autoplay_postfix in href:
                vid_refs.append(href)
            elif '/exercises/' in href:
                exercise_refs.append(href)

        for exercise_url in exercise_refs:
            try:
                print('exercise url:', exercise_url)
                exercise_name = exercise_url.split('/')[-1].split('?')[0]
                save_path = f"{exersice_dir}/{exercise_name}"
                urlretrieve(exercise_url, save_path)
                print(f"{save_path} is saved")
            except KeyboardInterrupt:
                raise
            except:
                print(f"\nException during processing {href}:", sys.exc_info()[0])

        for href in vid_refs:
            try:
                driver.get(href)
                time.sleep(timeout_sec)
                vid_elem = driver.find_element_by_tag_name('video')
                vid_url = vid_elem.get_attribute('src')
                print('video url:', vid_url)
                vid_name = vid_url.split('/')[-1].split('?')[0]
                save_path = f"{save_dir}/{vid_name}"
                urlretrieve(vid_url, save_path)
                print(f"{save_path} is saved")
            except KeyboardInterrupt:
                raise
            except:
                print(f"\nException during processing {href}:", sys.exc_info()[0])
    except KeyboardInterrupt:
        raise
    except:
        print(sys.exc_info()[0])

driver.quit()
