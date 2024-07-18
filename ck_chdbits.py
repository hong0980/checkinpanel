# -*- coding: utf-8 -*-
"""
cron: 50 59 23 * * *
new Env('CHDBits 签到');
"""

import re
import time
import answers
from utils import get_data
from notify_mtr import send
from datetime import datetime, timedelta

from selenium import webdriver
# from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

class Get:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument("start-maximized")
        options.add_argument('--disable-dev-shm-usage')

        service = webdriver.ChromeService(
            log_output='/tmp/chdbits.log',
            executable_path='/usr/bin/chromedriver',
            service_args=['--readable-timestamp']
        )
        driver = webdriver.Chrome(service=service, options=options)
        # stealth(driver,
        #     platform="Win32",
        #     fix_hairline=True,
        #     vendor="Google Inc.",
        #     languages=["zh-CN", "zh"],
        #     webgl_vendor="Intel Inc.",
        #     renderer="Intel Iris OpenGL Engine",
        # )

        def countdown():
            now = datetime.now()
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            sleep_seconds = (midnight - now).total_seconds()
            print(f'等待{int(sleep_seconds)}秒后执行！')
            time.sleep(sleep_seconds)

        try:
            driver.get('https://ptchdbits.co/torrents.php')
            for single_cookie in cookie.split('; '):
                name, value = single_cookie.split('=', 1)
                driver.add_cookie({'name': name, 'value': value})
            countdown()
            driver.get('https://ptchdbits.co/bakatest.php')
            html = driver.page_source

            if '每日签到' not in html:
                return f'账号({i})无法登录！可能Cookie失效，请重新修改'

            # name_element = WebDriverWait(driver, 5).until(
            #     EC.presence_of_element_located((By.CSS_SELECTOR, 'a[class="UltimateUser_Name"]'))
            # )
            # name = name_element.text
            name = re.findall(r'class="UltimateUser_Name"><b>(.*?)</b></a>', html, re.DOTALL)[0]
            res = f"--- {name} CHDBits 签到结果 ---\n"
            if '今天已经签过到了' not in html:
                msg = ''
                # question_id = driver.find_element(By.CSS_SELECTOR, 'input[name="questionid"]').get_attribute('value')
                question_id = re.findall(r'name="questionid" value="(\d+)">', html)[0]
                # question_element = driver.find_element(By.CSS_SELECTOR, 'td.text[align="left"]')
                # choices_element = driver.find_element(By.CSS_SELECTOR, 'td.text[style="white-space: nowrap;"]')
                # msg = f'<b>{question_id} 答题</b>\n{question_element.text}\n{choices_element.text}\n'

                answer_values = False
                if question_id:
                    answer_values = answers.get(question_id)

                if answer_values:
                    msg += '\n<b>使用答案：</b> \n'
                    for answer_value in answer_values:
                        driver.find_element(By.CSS_SELECTOR, f'input[value="{answer_value}"]').click()
                        question_text = re.findall(f'value="{answer_value}">(.*?)<', html)
                        question_text[0] = question_text[0].replace("&nbsp;", "")
                        msg += f'{question_text[0]}\n'
                    msg += '\n'

                else:
                    with open('/tmp/chdbits_随机答题.html.txt', 'a', encoding='utf-8') as file:
                        tbody = driver.find_element(By.XPATH, '//*[@id="outer"]/form/table/tbody')
                        tr_elements = tbody.find_elements(By.TAG_NAME, 'tr')
                        for i in range(min(2, len(tr_elements))):
                            file.write(tr_elements[i].get_attribute('outerHTML') + '\n')
                        file.write('\n')

                    from random import choice
                    values = ['1', '2', '4', '8']
                    random_value = choice(values)
                    driver.find_element(By.CSS_SELECTOR, f'input[value="{random_value}"]').click()

                    random_value_multi = ''
                    if '多选' in question_element.text:
                        remaining_values = [v for v in values if v != random_value]
                        random_value_multi = choice(remaining_values)
                        driver.find_element(By.CSS_SELECTOR, f'input[value="{random_value_multi}"]').click()
                    msg += f'使用随机值：{random_value} {random_value_multi}\n'

                driver.find_element(By.NAME, 'wantskip').click()
                now_time = datetime.now().time()
                res += f"{msg}<b><span style='color: green'>签到成功</span></b> {now_time}\n"

            qd_msg = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'font[color="white"]'))
            )
            if answer_values:
                with open('/tmp/chdbits_答案答题.html.txt', 'w', encoding='utf-8') as f:
                    f.write(html)
            res += f"<b><span style='color: {'orange' if '错误' in qd_msg.text else 'purple'}'>{qd_msg.text}</span></b>\n\n"
            pattern = r'使用</a>]: (.*?)\s*<font.*?分享率：</font>\s*(.*?)\s*<font.*?上传量：</font>\s*(.*?)\s*<font.*?下载量：</font>\s*(.*?)\s*<font.*?当前做种.*?>\s*(\d+)\s*<img.*?做种积分: </font>(.*?)</span>'
            result = re.findall(pattern, html, re.DOTALL)[0]
            res += (f'<b>{name} 账户信息：</b>\n'
                   f'魔力值：{result[0]}\n'
                   f'分享率：{result[1]}\n'
                   f'上传量：{result[2]}\n'
                   f'下载量：{result[3]}\n'
                   f'当前做种：{result[4]}\n'
                   f'做种积分：{result[5]}\n'
            )
            # import time
            # for i in range(5):
            #     screenshot_name = f'/tmp/3图片_chdbits_{i}.png'
            #     source_code_name = f'/tmp/3chdbits_{i}.html.txt'
            #     driver.save_screenshot(screenshot_name)
            #     with open(source_code_name, 'w', encoding='utf-8') as f:
            #         f.write(html)
            #     time.sleep(1)

        except TimeoutException as e:
            res += f"<b><span style='color: red'>超时异常：</span></b>\n{e}"
        except NoSuchElementException as e:
            res += f"<b><span style='color: red'>签到失败：</span></b>\n{e}"
        except WebDriverException as e:
            res += f"<b><span style='color: red'>WebDriver异常：</span></b>\n{e}"
        except Exception as e:
            res += f"<b><span style='color: red'>未知异常：</span></b>\n{e}"

        finally:
            driver.quit()

        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            sign_msg = self.sign(cookie, i)
            msg = f"{sign_msg}"
            msg_all += msg + "\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("CHDBITS", [])
    result = Get(check_items=_check_items).main()
    send("CHDBits 签到信息", result)
    # print(result)
