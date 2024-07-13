# -*- coding: utf-8 -*-
"""
cron: 1 0 * * *
new Env('ypojie');
"""
import re
from time import sleep
from utils import get_data
from notify_mtr import send

class Get:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(username, password, i):
        from selenium import webdriver
        from selenium_stealth import stealth
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import NoSuchElementException, TimeoutException
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # 无头模式
        options.add_argument('--no-sandbox')
        options.add_argument("start-maximized")
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        service = webdriver.ChromeService(
            log_output='/tmp/ypojie.log',
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

        try:
            res = ''
            url = 'https://www.ypojie.com/vip'
            driver.get(url)
            user_login = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "user_login"))
            )
            user_login.send_keys(username)
            driver.find_element(By.ID, "user_pass").send_keys(password)
            driver.find_element(By.ID, "wp-submit").click()

            if '登录 ‹ 易破解' in driver.page_source:
                return f'账号{i}登录不成功，用户名或密码可能错误。'

            driver.get(url)
            name = re.findall(r' Hi, (.*?) ', driver.page_source, re.DOTALL)
            res = f"---- {name[0]} 亿破姐 签到结果 ----\n"
            sign_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.usercheck.erphpdown-sc-btn'))
            )

            if '已签到' in sign_button.text:
                res += f"<b><span style='color: green'>今天已经签到</span></b>\n"
            else:
                try:
                    sign_button.click()
                    sleep(2)
                    driver.refresh()
                    res += f"<b><span style='color: green'>签到成功</span></b>\n"
                except Exception as e:
                    res += f"<b><span style='color: red'>签到失败</span></b>\n{e}"

            assets = driver.find_element(By.CLASS_NAME, 'erphpdown-sc-table').text
            res += assets

        except TimeoutException as e:
            res = f'等待超时：{e}'
        except NoSuchElementException as e:
            res = f'发生异常：{e}'
        except Exception as e:
            res = f'发生异常：{e}'
        finally:
            driver.quit()
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            username = check_item.get("username")
            password = check_item.get("password")
            msg = self.sign(username, password, i)
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("YPOJIE", [])
    result = Get(check_items=_check_items).main()
    send("亿破姐", result)
    # print(result)
