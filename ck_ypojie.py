# -*- coding: utf-8 -*-
"""
cron: 1 0 * * *
new Env('ypojie');
"""

from time import sleep
from utils import get_data
from notify_mtr import send

class Get:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(username, password):
        from selenium import webdriver
        from selenium_stealth import stealth
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import NoSuchElementException, TimeoutException
        result = ''
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # 无头模式
        options.add_argument('--no-sandbox')
        options.add_argument("start-maximized")
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        service = webdriver.ChromeService(
            log_output='/tmp/ypojie.log',
            executable_path='/usr/bin/chromedriver',
            service_args=['--readable-timestamp', '--disable-build-check']
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
            driver.get('https://www.ypojie.com/vip')
            sleep(3)
            # 找到用户名和密码输入框并输入用户名和密码
            username_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "user_login")))
            username_input.send_keys(username)
            sleep(1)
            password_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "user_pass")))
            password_input.send_keys(password)
            sleep(1)
            # 找到登录按钮并点击
            login_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "wp-submit")))
            login_button.click()
            sleep(1)
            driver.get('https://www.ypojie.com/vip')

            if '我的资产' in driver.page_source:
                assets = driver.find_element(By.CLASS_NAME, 'erphpdown-sc-table').text
                sign_button = driver.find_element(By.CLASS_NAME, "usercheck")

                if '已签到' in sign_button.text:
                    result += f'今天已经签到，{assets}'
                else:
                    try:
                        sign_button.click()
                        sleep(3)
                        driver.refresh()
                        assets = driver.find_element(By.CLASS_NAME, 'erphpdown-sc-table').text
                        result = f'签到成功，{assets}'
                    except TimeoutException:
                        result = '签到失败'
                    except Exception as e:
                        result = f'发生异常：{str(e)}'
            else:
                result = '用户名或密码出错，不能登录'
        except Exception as e:
            result += f'发生异常：{str(e)}'
        finally:
            driver.quit()
        return result

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            username = check_item.get("username")
            password = check_item.get("password")
            msg = f"---- 账号({i}) 亿破姐 签到结果 ----\n{self.sign(username, password)}"
            msg_all += msg + "\n\n"
        return msg_all


if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("YPOJIE", [])
    result = Get(check_items=_check_items).main()
    send("亿破姐", result)
    # print(result)
