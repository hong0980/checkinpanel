# -*- coding: utf-8 -*-
"""
cron: 0 0 * * *
new Env('chdbits 签到');
"""

import re
from utils import get_data
from notify_mtr import send
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

class Get:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie):
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

        try:
            res = ''
            driver.get('https://ptchdbits.co/torrents.php')
            for single_cookie in cookie.split('; '):
                name, value = single_cookie.split('=', 1)
                driver.add_cookie({'name': name, 'value': value})
            driver.get('https://ptchdbits.co/bakatest.php')

            if '每日签到' not in driver.page_source:
                return 'cookie失效'

            if '今天已经签过到了' not in driver.page_source:
                value1_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[value="1"]'))
                )
                value1_button.click()
                if '多选' in driver.page_source:
                    driver.find_element(By.CSS_SELECTOR, 'input[value="2"]').click()
                driver.find_element(By.CSS_SELECTOR, 'input[name="wantskip"]').click()
                res = f"<b><span style='color: green'>签到成功</span></b>\n"

            qd_msg = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//font[@color="white"]'))
            )
            res += f"<b><span style='color: orange'>{qd_msg.text}</span></b>\n\n"
            name = driver.find_element(By.CSS_SELECTOR, 'a[class="UltimateUser_Name"]')

            pattern = r'使用</a>]: (.*?)\s*<font.*?分享率：</font>\s*(.*?)\s*<font.*?上传量：</font>\s*(.*?)\s*<font.*?下载量：</font>\s*(.*?)\s*<font.*?当前做种.*?>\s*(\d+)\s*<img.*?做种积分: </font>(.*?)</span>'
            result = re.findall(pattern, driver.page_source, re.DOTALL)[0]
            res += (f'<b>{name.text} 账户信息：</b>\n'
                   f'魔力值：{result[0]}\n'
                   f'分享率：{result[1]}\n'
                   f'上传量：{result[2]}\n'
                   f'下载量：{result[3]}\n'
                   f'当前做种：{result[4]}\n'
                   f'做种积分：{result[5]}\n'
            )
            # import time
            # for i in range(5):
            #     screenshot_name = f'/tmp/图片_chdbits_{i}.png'
            #     source_code_name = f'/tmp/chdbits_{i}.html.txt'
            #     driver.save_screenshot(screenshot_name)
            #     with open(source_code_name, 'w', encoding='utf-8') as f:
            #         f.write(driver.page_source)
            #     time.sleep(1)

        except TimeoutException as e:
            res = f"<b><span style='color: red'>超时异常：</span></b>\n{e}"
        except NoSuchElementException as e:
            res = f"<b><span style='color: red'>签到失败：</span></b>\n{e}"
        except WebDriverException as e:
            res = f"<b><span style='color: red'>WebDriver异常：</span></b>\n{e}"
        except Exception as e:
            res = f"<b><span style='color: red'>未知异常：</span></b>\n{e}"

        finally:
            driver.quit()

        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            sign_msg = self.sign(cookie)
            msg = f"{sign_msg}"
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("CHDBITS", [])
    result = Get(check_items=_check_items).main()
    send("chdbits 签到信息", result)
    # print(result)
