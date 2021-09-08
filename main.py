from sys import exit
from time import sleep
from tqdm import trange

from pandas import DataFrame, option_context
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

import rsa
import getpass

from requests import request
from urllib.parse import quote
from yaml import load
from yaml import Loader


class User():
    def __init__(self, name: str=''):
        self.pubkey, self.privkey = rsa.newkeys(512)
        self.id = input('Your ID: ')
        self.passwd = rsa.encrypt(getpass.getpass('Your password: ').encode('utf-8'), self.pubkey)
        self.name = name
    
    def get_id(self):
        return self.id

    def get_passwd(self):
        return rsa.decrypt(self.passwd, self.privkey).decode('utf-8')


class Course():
    def __init__(self, id: str, name: str, score: float, lim_num: int, sel_num: int, sel_num1: int, ava_num: int, selected: bool, rkjs, sksj, skdd):
        self.id = id
        self.name = name
        self.score = score
        self.nums = [lim_num, sel_num, sel_num1, ava_num]
        self.selected = selected
        self.rkjs = rkjs
        self.sksj = sksj
        self.skdd = skdd


def server_chann_send(courses_to_select: list, courses_selected: list, courses_ava: list, token: str):
    post_url = 'https://sctapi.ftqq.com/{:s}.send?title={:s}&desp={:s}'
    ava_course_num = len(courses_ava)
    texts_toselect = map(lambda course: '[%s]%s 可选%d限选%d %s %s %s'%(course.id, course.name, course.nums[3], course.nums[0], course.rkjs, course.sksj, course.skdd), courses_to_select)
    text_ava = map(lambda course: '[%s]%s 可选%d限选%d %s %s %s'%(course.id, course.name, course.nums[3], course.nums[0], course.rkjs, course.sksj, course.skdd), courses_ava)
    text_selected = map(lambda course: '[%s]%s 可选%d限选%d %s %s %s'%(course.id, course.name, course.nums[3], course.nums[0], course.rkjs, course.sksj, course.skdd), courses_selected)
    title = '%d门课程可选！'%ava_course_num
    response = request("POST", post_url.format(token, quote(title), 
                quote('## 可选课程：\n\n- ' + '\n\n- '.join(text_ava) + '\n\n## 关注课程：\n\n- ' + '\n\n- '.join(texts_toselect) +'\n\n## 已选课程：\n\n- ' + '\n\n- '.join(text_selected))))
    print('发送状态：', response)


def loggin_to_BNU(driver: WebDriver, user: User):
    # input id
    id_inputbox = driver.find_element_by_id('un')
    id_inputbox.clear()
    id_inputbox.send_keys(user.get_id())
    # input password
    passwd_inputbox = driver.find_element_by_id('pd')
    passwd_inputbox.clear()
    passwd_inputbox.send_keys(user.get_passwd())
    # loggin
    passwd_inputbox.send_keys(Keys.RETURN)
    return 1


def show_course_info(courses: list, title: str):
    d = {
        'ID'    :   map(lambda c: c.id, courses)            ,
        '课程'  :   map(lambda c: c.name, courses)           ,
        '学分'  :   map(lambda c: c.score, courses)          ,
        '限选人数'  :   map(lambda c: c.nums[0], courses)    ,
        '已选人数'  :   map(lambda c: c.nums[1], courses)    ,
        '免听人数'  :   map(lambda c: c.nums[2], courses)    ,
        '可选人数'  :   map(lambda c: c.nums[3], courses)    ,
        '是否已选中':   map(lambda c: '是' if c.selected else '否', courses)
    }
    df = DataFrame(data=d)
    print(title)
    with option_context('display.max_rows', None, 'display.max_columns', None):
        print(df)


def main():
    # init by config
    with open('./config.yml', 'r', encoding='utf-8') as config_file:
        config_data = load(config_file, Loader=Loader)
    courses_to_select = config_data['courses_to_select']
    server_chann_token = config_data['server_chann_token']
    stop_when_found = config_data['stop_when_found']
    courses_to_stop_when_found = config_data['courses_to_stop_when_found']
    refresh_time_sep = float(config_data['refresh_time_sep'])
    number_of_refresh_times = int(config_data['number_of_refresh_times'])
    if number_of_refresh_times == 114514:
        print('你不对劲？')
    if number_of_refresh_times == 1145141919810:
        while True:
            print('啊', end='')
        exit()  # 虽然没什么用
    if number_of_refresh_times <= 0:
        print('?')
        exit()
    # create user
    user = User('test')
    # open driver
    driver = webdriver.Firefox()
    driver.get('http://zyfw.bnu.edu.cn/MainFrm.html')
    if '北京师范大学统一身份认证' in driver.title:
        assert loggin_to_BNU(driver, user), "Loggin to BNU failed"
    driver.implicitly_wait(20)
    driver.switch_to.frame("frmbody")
    but_网上选课 = driver.find_element_by_xpath('/html/body/table/tbody/tr/td[1]/table/tbody/tr[2]/td/table/tbody/tr/td/div[2]/table/tbody/tr[5]')
    ActionChains(driver).move_to_element(but_网上选课).click(but_网上选课).perform()
    driver.implicitly_wait(10)
    driver.switch_to.frame('frmDesk')
    but_选公共选修课 = driver.find_element_by_xpath('//*[@id="module1803"]')
    ActionChains(driver).move_to_element(but_选公共选修课).click(but_选公共选修课).perform()
    driver.implicitly_wait(10)
    check_限未选满的课程 = driver.find_element_by_xpath('//*[@id="xwxmkc"]')
    ActionChains(driver).move_to_element(check_限未选满的课程).click(check_限未选满的课程).perform()
    driver.implicitly_wait(2)
    but_检索 = driver.find_element_by_xpath('//*[@id="btnQry"]')
    ActionChains(driver).move_to_element(but_检索).click(but_检索).perform()
    driver.implicitly_wait(10)
    for t in range(number_of_refresh_times):
        print(f'Trail {t} ...')
        selected_courses = []
        to_select_courses = []
        driver.switch_to.frame('frmReport')
        total_page = int(driver.find_element_by_xpath('//*[@id="totalPage"]').text)
        for i in range(total_page):
            print(f'Finding page {i+1} ...')
            driver.find_element_by_xpath('//*[@id="goPageNo"]').clear()
            driver.find_element_by_xpath('//*[@id="goPageNo"]').send_keys('%d'%(i+1))
            driver.find_element_by_xpath('//*[@id="goPageNo"]').send_keys(Keys.RETURN)
            driver.implicitly_wait(5)
            sleep(5)
            total_page = int(driver.find_element_by_xpath('//*[@id="totalPage"]').text)
            row_in_this_page = len(driver.find_elements_by_xpath('/html/body/div[1]/table/tbody/tr'))
            for row in trange(row_in_this_page):
                row_id_format = '//*[@id="tr%d_{:s}"]'%(row+100*i)
                try:
                    course_name_full = driver.find_element_by_xpath(row_id_format.format('kc')).text
                except:
                    continue
                if course_name_full == '':
                    continue
                course_id = course_name_full.split(']')[0].split('[')[-1]
                course_name = course_name_full.split(']')[1]
                course_score = float(driver.find_element_by_xpath(row_id_format.format('xf')).text)
                course_xxrs = int(driver.find_element_by_xpath(row_id_format.format('xxrs')).text)
                course_yxrs_full = driver.find_element_by_xpath(row_id_format.format('yxrs')).text
                course_yxrs, course_mtrs = list(map(int, course_yxrs_full.split('/')))
                course_kxrs = int(driver.find_element_by_xpath(row_id_format.format('kxrs')).text)
                course_xz = (driver.find_element_by_xpath(row_id_format.format('xz')).text == "已选中")
                course_rkjs = driver.find_element_by_xpath(row_id_format.format('rkjs')).text
                course_sksj = driver.find_element_by_xpath(row_id_format.format('sksj')).text
                course_skdd = driver.find_element_by_xpath(row_id_format.format('skdd')).text
                if course_xz:
                    selected_courses.append(Course(course_id, course_name, course_score, course_xxrs, course_yxrs, course_mtrs, course_kxrs, True, course_rkjs, course_sksj, course_skdd))
                    continue
                if course_id in courses_to_select:
                    to_select_courses.append(Course(course_id, course_name, course_score, course_xxrs, course_yxrs, course_mtrs, course_kxrs, False, course_rkjs, course_sksj, course_skdd))
        courses_ava = list(filter(lambda course: course.nums[3] > 0, to_select_courses))
        show_course_info(selected_courses, '已选课程')
        show_course_info(to_select_courses, '待选课程')
        show_course_info(courses_ava, "可选课程")
        driver.switch_to.parent_frame()
        # send info to phone if inneed
        ava_courses_num = len(courses_ava)
        if ava_courses_num > 0:
            server_chann_send(to_select_courses, selected_courses, courses_ava, server_chann_token)
            if stop_when_found:
                # exit
                for course in courses_ava:
                    if course.id in courses_to_stop_when_found:
                        driver.close()
                        exit()
        sleep(refresh_time_sep)
    
    driver.close()
    pass 


if __name__ == "__main__":
    main()