# -*- coding: utf-8 -*-
"""
Created on Sun Oct 27 21:11:25 2019

@author: Aleh
"""

from bs4 import BeautifulSoup
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
import re
import json
import traceback


timeout_sec = 5


def get_valid_filename(s):
    return re.sub(r'[^-\w\s.,]', '', s).strip()

def file_name_from_url(url):
    return url.split('/')[-1].split('?')[0]

def check_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"'{file_name_from_url(path)}' is created")

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


def download_file(url, save_path):
    if os.path.exists(save_path):
        print(f"'{file_name_from_url(save_path)}' was already downloaded")
    else:
        urlretrieve(url, save_path)
        print(f"'{file_name_from_url(save_path)}' is saved")


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


def get_chapters(html):
    chapters = []
    try:
        bsObj = BeautifulSoup(html, 'html.parser')
        chapter_items = bsObj.find('ul', {'class':"course-toc__list"}).findAll('li')
        for chapter_item in chapter_items:
            chapter = {}
            chapter['header'] = chapter_item.find('div', {'class':"course-chapter__header"}).text.strip()
            items = chapter_item.find('div', {'class':"course-chapter__items"}).findAll('a', {'data-control-name':"course_video_route"})
            chapter['items'] = []
            for item in items:
                duration = item.find('span', {'class':"duration"})
                if duration:
                    video = {}
                    href = item['href']
                    if href.startswith('/learning'):
                        href = 'https://www.linkedin.com' + href
                    video['ref'] = href
                    video['title'] = duration.parent.parent.find(text=True).strip()
                    video['duration'] = duration.text.strip()
                    chapter['items'].append(video)
            chapters.append(chapter)
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        print(f"\nException in get_chapters:", repr(ex))
        traceback.print_exc(file=sys.stdout)
    return chapters


def get_raw_subtitles(html):
    subs = []
    try:
        bsObj = BeautifulSoup(html, 'html.parser')
        vid_name = bsObj.find('span', {'class':"embed-entity__video-title"}).text.strip()
        for div in bsObj.findAll('div'):
            if 'data-video-id' in div.attrs:
                if vid_name == div.find('span', {'class':"duration"}).parent.parent.find(text=True).strip():
                    # video id like 'urn:li:lyndaVideo:(urn:li:lyndaCourse:5030978,2810951)'
                    full_id_str = div['data-video-id']
                    #vid_id = full_id_str.split(',')[-1].strip(')').strip()
                    break

        for code in bsObj.findAll('code'):
            try:
                code_json = json.loads(code.text)
                if 'included' in code_json:
                    for item in code_json['included']:
                        if 'transcriptStartAt' in item and full_id_str in item['$id']:
                            subs.append(item)
            except:
                pass
        subs.sort(key=lambda x: x['transcriptStartAt'])

    except KeyboardInterrupt:
        raise
    except Exception as ex:
        print(f"\nException in get_raw_subtitles:", repr(ex))
        traceback.print_exc(file=sys.stdout)
    return subs


def sub_format_time_from_ms(time_ms: int):
    sec, ms = divmod(time_ms, 1000)
    minutes, sec = divmod(sec, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{sec:02}:{ms:03}"


def save_subtitles(subs, file_path):
    lines = []
    for num, sub in enumerate(subs[:-1], start=1):
        lines.append(str(num))
        lines.append(f"{sub_format_time_from_ms(sub['transcriptStartAt'])} --> "
                        f"{sub_format_time_from_ms(subs[num]['transcriptStartAt'] - 10)}")
        lines.append(sub['caption'])
        lines.append('')
    # last time stamp is special
    lines.append(f"{len(subs)}")
    #TODO add video duration instead of hardcoded 5 sec duration
    lines.append(f"{sub_format_time_from_ms(subs[-1]['transcriptStartAt'])} --> "
                    f"{sub_format_time_from_ms(subs[-1]['transcriptStartAt'] + 5000)}")
    lines.append(subs[-1]['caption'])
    lines.append('')

    save_html('\n'.join(lines), file_path)

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
                check_directory(save_dir)

                chapters = None
                tabs = driver.find_elements_by_tag_name('artdeco-tab')
                for tab in tabs:
                    if content_tab in tab.get_attribute('innerHTML'):
                        tab.click()
                        wait_for_js(driver)
                        save_html(driver.page_source, f"{save_dir}/{content_tab}.html")
                        chapters = get_chapters(driver.page_source)
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
                    check_directory(exersice_dir)

                    for exercise_url in exercise_refs:
                        try:
                            #print('exercise url:', exercise_url)
                            exercise_name = file_name_from_url(exercise_url)
                            save_path = f"{exersice_dir}/{exercise_name}"
                            download_file(exercise_url, save_path)
                        except KeyboardInterrupt:
                            raise
                        except Exception as ex:
                            print(f"\nException during processing exercise {exercise_url}:", repr(ex))
                            traceback.print_exc(file=sys.stdout)
                else:
                    print(f"Warning! {file_name_from_url(course_url)} does't contains {exersise_tab}")

                if chapters:
                    for idx, chapter in enumerate(chapters):
                        vid_dir_name = get_valid_filename(chapter['header'])
                        if not str.isdigit(vid_dir_name[0]):
                            vid_dir_name = f"{idx}. {vid_dir_name}"
                            print(f"chapter header to folder name: '{chapter['header']}' -> '{vid_dir_name}'")
                        vid_dir_path = f"{save_dir}/{vid_dir_name}"
                        check_directory(vid_dir_path)

                        for vid_idx, vid_item in enumerate(chapter['items']):
                            try:
                                file_name = get_valid_filename(f"{vid_item['title']}.mp4")
                                if not str.isdigit(file_name[0]):
                                    file_name = f"{str(vid_idx+1).zfill(2)}. {file_name}"
                                save_path = f"{vid_dir_path}/{file_name}"
                                if os.path.exists(save_path):
                                    print(f"'{vid_dir_name}/{file_name}' was already downloaded")
                                    continue

                                driver.get(vid_item['ref'])
                                wait_for_js(driver)
                                time.sleep(timeout_sec)
                                # save video page, can be usefull for later data extration
                                save_html(driver.page_source, os.path.splitext(save_path)[0] + '.html')

                                vid_elem = driver.find_element_by_tag_name('video')
                                vid_url = vid_elem.get_attribute('src')
                                download_file(vid_url, save_path)

                                subs = get_raw_subtitles(driver.page_source)
                                transcription = ' '.join([sub['caption'] for sub in subs])
                                save_html(transcription, os.path.splitext(save_path)[0] + '.txt')
                                save_subtitles(subs, os.path.splitext(save_path)[0] + '.srt')
                            except KeyboardInterrupt:
                                raise
                            except Exception as ex:
                                print(f"\nException during processing video {vid_item['ref']}:", repr(ex))
                                traceback.print_exc(file=sys.stdout)

                    save_html(driver.page_source, f"{save_dir}/{content_tab}.html")
                else:
                    print(f"Warning! {file_name_from_url(course_url)} does't contains {content_tab}")

# v0.1 video saving
#                if vid_refs:
#                    for href in vid_refs:
#                        try:
#                            driver.get(href)
#                            time.sleep(timeout_sec)
#                            vid_elem = driver.find_element_by_tag_name('video')
#                            vid_url = vid_elem.get_attribute('src')
#                            #print('video url:', vid_url)
#                            vid_name = file_name_from_url(vid_url)
#                            save_path = f"{save_dir}/{vid_name}"
#                            download_file(vid_url, save_path)
#                        except KeyboardInterrupt:
#                            raise
#                        except:
#                            print(f"\nException during processing {href}:", sys.exc_info()[0])
#
#                    save_html(driver.page_source, f"{save_dir}/info.html")
#                else:
#                    print(f"Warning! {file_name_from_url(course_url)} does't contains {content_tab}")
            except KeyboardInterrupt:
                raise
            except Exception as ex:
                print(f"\nException during processing course {course_url}:", repr(ex))
                traceback.print_exc(file=sys.stdout)


if __name__ == '__main__':
    cmdline_args = Arguments()

    user_email = cmdline_args.get_user_email()
    user_password = cmdline_args.get_user_password()
    base_dir = cmdline_args.get_content_derectory()
    courses = cmdline_args.get_courses() # ['https://www.linkedin.com/learning/c-plus-plus-design-patterns-creational']
    courses = list(map(lambda course: course if course.startswith('https:') \
                       else 'https://www.linkedin.com/learning/' + course, courses))
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
