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


timeout_sec = 5


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


def file_name_from_url(url):
    return url.split('/')[-1].split('?')[0]


def download_file(url, save_path):
    if os.path.exists(save_path):
        print(f"{save_path} was already downloaded")
    else:
        urlretrieve(url, save_path)
        print(f"{save_path} is saved")


class Arguments:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('-email', '-login', help="user's linkedin login (email)")
        self.parser.add_argument('-password', '-p', help="user's linkedin password")
        self.parser.add_argument('-dir', '-folder', '-directory', help="directory to store content")
        self.parser.add_argument('-driver', '-geckodriver', help="full geckodriver.exe path")
        self.parser.add_argument('--courses', nargs='+', help="linkedin-learning courses' links to download")
        self.args = self.parser.parse_args()

    def get_driver_path(self):
        if self.args.driver:
            return self.args.driver
        return 'geckodriver.exe' # should be in the same folder as the script

    def get_user_email(self):
        if not self.args.email:
            raise ValueError("-email or -login command line argument should be provided")
        return self.args.email

    def get_user_password(self):
        if not self.args.password:
            raise ValueError("-p or -password command line argument should be provided")
        return self.args.password

    def get_content_derectory(self):
        if self.args.dir:
            return self.args.dir.replace('\\','/').rstrip('/')
        return ''

    def get_courses(self):
        if self.args.courses:
            return self.args.courses
        return []


def get_logged_in_driver(driver_path, user_email, user_password, login_link):
    driver = webdriver.Firefox(executable_path = driver_path)
    driver.set_page_load_timeout(50)
    driver.maximize_window()

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
    return driver


class Downloader():
    def __init__(self, web_driver):
        self.autoplay_postfix = "?autoplay=true"
        self.driver = web_driver
        self.courses = []
        self.directory_to_store = ''

    def download(self):
        driver = self.driver
        exersise_tab = 'Exercise Files'
        content_tab = 'Contents'
        for course_url in self.courses:
            try:
                driver.get(course_url)
                wait_for_js(driver)
                time.sleep(timeout_sec)

                save_dir = f"{self.directory_to_store}/{course_url.split('/')[-1]}"
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)

                tabs = driver.find_elements_by_tag_name('artdeco-tab')
                for tab in tabs:
                    if content_tab in tab.get_attribute('innerHTML'):
                        tab.click()
                        wait_for_js(driver)
                        save_html(driver.page_source, f"{save_dir}/info.html")
                    elif exersise_tab in tab.get_attribute('innerHTML'):
                        tab.click()
                        wait_for_js(driver)
                        break

                elemets_a = driver.find_elements_by_tag_name('a')
                vid_refs = []
                exercise_refs = []
                for a in elemets_a:
                    href = a.get_attribute('href')
                    if course_url in href and self.autoplay_postfix in href:
                        vid_refs.append(href)
                    elif '/exercises/' in href:
                        exercise_refs.append(href)

                if exercise_refs:
                    exersice_dir = f"{save_dir}/{exersise_tab}"
                    if not os.path.exists(exersice_dir):
                        os.makedirs(exersice_dir)

                    for exercise_url in exercise_refs:
                        try:
                            #print('exercise url:', exercise_url)
                            exercise_name = file_name_from_url(exercise_url)
                            save_path = f"{exersice_dir}/{exercise_name}"
                            download_file(exercise_url, save_path)
                        except KeyboardInterrupt:
                            raise
                        except:
                            print(f"\nException during processing {href}:", sys.exc_info()[0])
                else:
                    print(f"Warning! {file_name_from_url(course_url)} does't contains {exersise_tab}")

                if vid_refs:
                    for href in vid_refs:
                        try:
                            driver.get(href)
                            time.sleep(timeout_sec)
                            vid_elem = driver.find_element_by_tag_name('video')
                            vid_url = vid_elem.get_attribute('src')
                            #print('video url:', vid_url)
                            vid_name = file_name_from_url(vid_url)
                            save_path = f"{save_dir}/{vid_name}"
                            download_file(vid_url, save_path)
                        except KeyboardInterrupt:
                            raise
                        except:
                            print(f"\nException during processing {href}:", sys.exc_info()[0])

                    save_html(driver.page_source, f"{save_dir}/info.html")
                else:
                    print(f"Warning! {file_name_from_url(course_url)} does't contains {content_tab}")
            except KeyboardInterrupt:
                raise
            except:
                print(f"\nException during processing {course_url}:", sys.exc_info()[0])


if __name__ == '__main__':
    cmdline_args = Arguments()

    user_email = cmdline_args.get_user_email()
    user_password = cmdline_args.get_user_password()
    base_dir = cmdline_args.get_content_derectory()
    courses = cmdline_args.get_courses() # ['https://www.linkedin.com/learning/c-plus-plus-design-patterns-creational']
    print('courses to download:', courses)

    # the next link doesn't work with driver
    # driver.get("https://www.linkedin.com/learning/login?redirect=https%3A%2F%2Fwww.linkedin.com%2Flearning%2F%3Ftrk%3Ddefault_guest_learning&trk=sign_in")
    login_link = 'https://www.linkedin.com/uas/login?fromSignIn=true&trk=learning&_l=en_US&uno_session_redirect=https%3A%2F%2Fwww.linkedin.com%2Flearning%2F%3Ftrk%3Ddefault_guest_learning&session_redirect=%2Flearning%2FloginRedirect.html&is_enterprise_authed='
    driver = get_logged_in_driver(cmdline_args.get_driver_path(), user_email, user_password, login_link)

    downloader = Downloader(driver)
    downloader.courses = courses
    downloader.directory_to_store = base_dir
    downloader.download()

    driver.quit()
    print('finish')
