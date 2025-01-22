# -*- coding: utf-8 -*-
"""
cron: 10 9,15 * * *
new Env('V2EX 签到');
"""

import re
from utils import get_data
from notify_mtr import send
from datetime import datetime
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

class V2ex:
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
            log_output='/tmp/v2ex.log',
            executable_path='/usr/bin/chromedriver',
            service_args=['--readable-timestamp']
        )

        driver = webdriver.Chrome(service=service, options=options)
        stealth(driver,
            platform="Win32",
            fix_hairline=True,
            vendor="Google Inc.",
            languages=["zh-CN", "zh"],
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
        )

        res, msg = '', ''
        try:
            driver.get('https://www.v2ex.com/signin')
            for single_cookie in cookie.split('; '):
                name, value = single_cookie.split('=', 1)
                driver.add_cookie({'name': name, 'value': value})
            driver.get('https://www.v2ex.com/mission/daily')

            if '注册' in driver.page_source:
                return f'账号({i})无法登录！可能Cookie失效，请重新修改'

            sign_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="button"]'))
            )
            name_element = driver.find_element(By.XPATH, '//span[@class="bigger"]')
            msg = f"---- {name_element.text} V2EX 签到状态 ----\n"

            res = f"{msg}<b><span style='color: green'>今天已经签到过了</span></b>"
            if '领取 X 铜币' in sign_button.get_attribute('value'):
                sign_button.click()
                res = f"{msg}<b><span style='color: green'>签到成功</span></b>"

            money_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[value='查看我的账户余额']"))
            )
            cell = re.findall(r'>(已连续登录.*?天)<', driver.page_source)[0]
            money_button.click()

            formatted_date = datetime.now().strftime('%Y%m%d')
            gray = re.findall(f'{formatted_date}.*?(每日登录奖励.*?)</span>', driver.page_source)
            money = driver.find_element(By.CSS_SELECTOR, "#money .balance_area").text.replace('\n', '').strip()
            res += f"\n{cell}\n{gray[0]}\n当前账户余额：{money} 铜币"

        except TimeoutException as e:
            res = f"{msg}<b><span style='color: red'>超时异常：</span></b>\n{e}"
        except NoSuchElementException as e:
            res = f"{msg}<b><span style='color: red'>签到失败：</span></b>\n{e}"
        except WebDriverException as e:
            res = f"{msg}<b><span style='color: red'>WebDriver异常：</span></b>\n{e}"
        except Exception as e:
            res = f"{msg}<b><span style='color: red'>未知异常：</span></b>\n{e}"

        finally:
            # driver.get('https://bot.sannysoft.com/')
            # total_height = driver.execute_script("return document.body.scrollHeight")
            # driver.set_window_size(1920, total_height)
            # driver.save_screenshot('/tmp/screenshot.png')
            driver.quit()
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            msg = self.sign(cookie, i)
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    result = V2ex(check_items=get_data().get("V2EX", [])).main()
    if '签到成功' in result:
        send("V2EX 签到", result)
    else:
        print(result)
