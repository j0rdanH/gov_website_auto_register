import time
import os
import win32con
import win32api
import ddddocr
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import re
import argparse
import crawl_url

# 问题：有些按钮不是button而是div或者input

''' 很多信息是以placeholder形式展现，比如“身份证有效期” '''
def get_placeholder(html):
    try:
        placeholder_content = re.findall(r'placeholder=\".*?\"', html)
        return placeholder_content
    except:
        print(html+' 没有placeholder')

def judge_auth_type(info)->dict:
    auth_type = {'id_num1': '身份证号', 'id_num2': '证件号', 'valid': '有效', 'face': '人脸', 'pic': '照片'}
    flag_dict = {'auth': False, 'id_num': False, 'valid': False, 'face': False, 'pic': False}
    for key, value in auth_type.items():
        for it in info:
            if value in it:
                flag_dict['auth'] = True
                if value == '证件号' or value == '身份证号':
                    flag_dict['id_num'] = True
                else:
                    flag_dict[key] = True
    # print(flag_dict)
    return flag_dict
    '''
    if flag_dict['auth'] is False:
        print('页面没有实名验证')
        return
    elif flag_dict['face'] or flag_dict['pic']:
        print('需要人脸核验或上传身份证照片')
        return
    else:
        print('身份证有效期核验')
        return
    '''
'''获取所有输入框的id，并与其placeholder形成键值对，用于自动填写'''
def get_all_input(html) -> list:
    input_list = re.findall(r'<input.*?>', html)
    input_with_placeholder = []
    for item in input_list:
        if 'placeholder' in item:
            input_with_placeholder.append(item)
    print(input_with_placeholder)
    return input_with_placeholder

def get_all_button_content(html)->list:
    button_content = re.findall(r'<button.*?</button>', html)
    # print(button_content)
    button_content_list = []
    for button in button_content:
        soup = BeautifulSoup(button)
        soup = soup.get_text()
        # print(soup)
        button_content_list.append(soup.replace(' ', ''))
        # return soup
    return button_content_list


# 获取短信验证码，有一些不是button而是span/input等
'''undone'''

def get_smscode_button_class(html)->str:
    s = re.findall(r'获取.*?验证码', html)
    print(s)
    # print(type(html))
    for i in s:
        if '手机' in i or '短信' in i or '获取验证码' in i:
            num = html.find(i)
            for j in range(num, -1, -1):
                if html[j] == '<':
                    tag_begin = j
                    break





# 用于获取验证码图片以及自动识别,目前仅适用于静态加载的字母/数字验证码
# urllib访问图片src会导致验证码的改变，这里选择用webdriver右键保存
def valid_code_get(html, web_driver)->str:
    img_list = re.findall(r'<img.*?>', html)
    code_img = ''
    for img_item in img_list:
        print(img_item)
        if 'code' in img_item:
            code_img = img_item
            break
    code_img_id = re.findall(r'id=\".*?\"', code_img)[0][4:-1]

    print(code_img_id)

    img = web_driver.find_element(by=By.ID, value=code_img_id)
    ActionChains(web_driver).context_click(img).perform()

    '''将图片保存到默认路径'''
    win32api.keybd_event(40, 0, 0, 0)
    win32api.keybd_event(40, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(40, 0, 0, 0)
    win32api.keybd_event(40, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(0x0D, 0, 0, 0)
    win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)
    # 此处sleep为了防止线程混乱
    time.sleep(0.5)
    #win32api.keybd_event(98, 0, 0, 0)
    #win32api.keybd_event(98, 0, win32con.KEYEVENTF_KEYUP, 0)

    win32api.keybd_event(0x31, 0, 0, 0)
    win32api.keybd_event(0x31, 0, win32con.KEYEVENTF_KEYUP, 0)

    win32api.keybd_event(0x0D, 0, 0, 0)
    win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(0x0D, 0, 0, 0)
    win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)


    # web_driver.find_element(by=By.ID, value=code_img_id).context_click()
    ocr = ddddocr.DdddOcr()
    time.sleep(0.5)         # 图片下载完毕才读取
    res = ''
    path = 'C:\\Users\\think\\Downloads\\'
    name = os.listdir(path)
    code_path = ''
    for j in name:
        if 'jpg' in j or 'png' in j:
            code_path = path+j
            break
    with open(code_path, 'rb') as f:
        img_bytes = f.read()
        res = ocr.classification(img_bytes)
        print(res)
    f.close()
    for i in name:
        if 'jpg' in i or 'png' in i:
            os.remove(path + i)
    return res


def reg_temp_judge(html):
    button_content_list = get_all_button_content(html)
    placeholder_content = get_placeholder(html)
    # print(placeholder_content)
    flag_dict = judge_auth_type(placeholder_content)
    print(flag_dict)
    if '下一步' in button_content_list:
        if flag_dict['face'] or flag_dict['pic']:
            print('需要人脸核验或上传身份证照片,无法实现抢注')
            return
        else:
            print('需要填写信息，无法确定')
    elif '注册' in button_content_list or '提交' in button_content_list:
        if not flag_dict['auth']:
            print('页面没有实名验证或者有其他验证方式，需要人工检查')
        elif flag_dict['face'] :
            print('需要人脸核验,无法实现抢注')
            return
        elif flag_dict['pic']:
            print('需要上传身份证照片,无法实现抢注')
            return
        elif flag_dict['valid']:
            print('身份证有效期核验,可以抢注')
            return
        else:
            print('姓名身份证号验证，可以抢注')
            return
    elif not button_content_list:
        print('页面中无按钮元素，需要人工检查')
    else:
        print('出现其他类型提交方式，请人工验证')

#### 全部加上try是因为有时候html中会有一些元素，但是页面上并没有体现出来，webdriver填写会报错
def auto_fill_input(html, web_driver):
    input_list = get_all_input(html)
    fill_tips = {}          # 保存id:placeholder的键值对，id用于定位，placeholder用于提示应该填入什么信息
    for input_item in input_list:
        input_id_list = re.findall(r'id=\".*?"', input_item)
        input_id = input_id_list[0][4:-1]
        # print(input_id)
        placeholder_content_list = get_placeholder(input_item)
        placeholder = placeholder_content_list[0][13:-1]
        # print(placeholder)
        '''防止出现类似甘肃政务的情况，下拉菜单导致一个id对应多个placeholder'''
        if input_id not in fill_tips:
            fill_tips[input_id] = placeholder
    print(fill_tips)
    '''信息自动填写'''
    for id, placeholder in fill_tips.items():
        if '字母开头' in placeholder:       ### 需要修改，普遍性不强
            try:
                web_driver.find_element(by=By.ID, value=id).send_keys('asd453421_')
                continue
            except:
                pass

        if '姓名' in placeholder:
            try:
                web_driver.find_element(by=By.ID, value=id).send_keys('侯乔聃')
                continue
            except:
                pass
        if '身份证号码' in placeholder:
            try:
                web_driver.find_element(by=By.ID, value=id).send_keys('320324199807187033')
                continue
            except:
                pass
        if '手机号' in placeholder:
            try:
                web_driver.find_element(by=By.ID, value=id).send_keys('15805163258')
                continue
            except:
                pass
        if '确认密码' in placeholder or 'password' in id or '再次' in placeholder:
            try:
                web_driver.find_element(by=By.ID, value=id).send_keys('asd453421_')
                continue
            except:
                pass
        if '开始日期' in placeholder:
            try:
                web_driver.find_element(by=By.ID, value=id).send_keys('2014-08-26')
                continue
            except:
                pass
        if '结束日期' in placeholder:
            try:
                web_driver.find_element(by=By.ID, value=id).send_keys('2024-08-26')
                continue
            except:
                pass
        if '图形验证码' in placeholder or '图片验证码' in placeholder:
            try:
                valid_code = valid_code_get(html, web_driver)  # 获取图形验证码
                web_driver.find_element(by=By.ID, value=id).send_keys(valid_code)
                web_driver.find_element(by=By.ID, value='sendcode').click()
                continue
            except:
                pass

#####  目前调研所有网站找回密码都为“下一步”
def pwd_temp_judge(html):
    button_content_list = get_all_button_content(html)
    if '下一步' in button_content_list:
        print('有多步流程，需要人工验证')
    elif not button_content_list:
        print('未检测到按钮，需要人工验证')
    else:
        pass


parser = argparse.ArgumentParser(description='选择功能，输入网址')
parser.add_argument('--function', '-F', help='密码找回（pwd）/注册页面（register），默认为注册页面', default='register')
parser.add_argument('--url', '-U', help='输入网址', default='https://ywtb.mps.gov.cn/newhome/register/grzc?Pattern=normalPattern')
args = parser.parse_args()


if __name__ == '__main__':
    chromeoptions = webdriver.ChromeOptions()
    # prefs = {"download.default_directory": "D:\\privacy_project\\auto_register\\valid_code"}
    # 将自定义设置添加到Chrome配置对象实例中
    chromeoptions.add_experimental_option('excludeSwitches', ['enable-logging'])
    s = Service('C:\\Program Files\\Google\\Chrome\\Application\\chromedriver.exe')
    dri = webdriver.Chrome(service=s, options=chromeoptions)

    #######   crawl_url.url_crawler(target='')

    # 打开浏览器
    #chrome_browser = webdriver.Chrome(chrome_options=option, executable_path='F:\python\chrome驱动\chromedriver.exe')
    #url = 'https://ywtb.mps.gov.cn/newhome/register/grzc?Pattern=normalPattern'
    # url = 'https://zwfw.gansu.gov.cn/gsjis/sso/register?client_id=zygszwfww&utype=0'
    #url = 'https://user.mct.gov.cn/idm/user/reg?servicecode=wlzwfwmh&gourl=http%3A%2F%2Fzwfw.mct.gov.cn%3A80%2F'
    # url = 'https://ucs-sso.digitalhainan.com.cn/register'

    url = args.url
    dri.get(url)
    time.sleep(0.3)     # 解决动态渲染问题
    page_html = dri.page_source
    # print(page_html)
    if args.function == 'register':
        reg_temp_judge(page_html)
    else:
        pwd_temp_judge(page_html)



    #placeholder_content = get_placeholder(page_html)
    #print(placeholder_content)
    #judge_auth_type(placeholder_content)
    # get_all_button_content(page_html)
    # auto_fill_input(page_html, dri)

    # get_smscode_button_class(page_html)

