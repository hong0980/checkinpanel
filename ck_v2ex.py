# -*- coding: utf-8 -*-
"""
cron: 10 11 * * *
new Env('V2EX');
"""

from utils import get_data
from notify_mtr import send

class V2ex:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie):
        from selenium import webdriver
        from selenium_stealth import stealth
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # 无头模式
        options.add_argument('--no-sandbox')
        options.add_argument("start-maximized")
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        service = webdriver.ChromeService(
            log_output='/tmp/v2ex.log',
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
            result = ''
            driver.get('https://www.v2ex.com/')
            for single_cookie in cookie.split('; '):
                name, value = single_cookie.split('=', 1)
                driver.add_cookie({'name': name, 'value': value})
            driver.refresh()

            if '创作新主题' in driver.page_source:
                driver.get('https://www.v2ex.com/mission/daily')
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'super')))
                sign_button = driver.find_element(By.CLASS_NAME, 'super')
                result = "<b><span style='color: green'>今天已经签到</span></b>\n"
                if '领取' in sign_button.get_attribute('value'):
                    sign_button.click()
                    driver.refresh()
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'super')))
                    sign_button = driver.find_element(By.CLASS_NAME, 'super')
                    result = "<b><span style='color: green'>签到成功</span></b>\n"

                cell = driver.find_element(By.XPATH, '//div[@id="Main"]/div[2]/div[3]').text
                sign_button.click()
                driver.refresh()
                gray = driver.find_element(By.CSS_SELECTOR, 'table.data td span.gray').text.strip()
                money = driver.find_element(By.XPATH, '//*[@id="Main"]/div[2]/div[4]/table/tbody/tr[2]/td[4]').text
                result += f"{gray}\n{cell}\n余额：{money} 铜币"
            else:
                result += '无法登录！可能Cookie失效，请重新修改'

        except TimeoutException as e:
            result += f"<b><span style='color: red'>超时异常：</span></b>\n{e}"
        except NoSuchElementException as e:
            result += f"<b><span style='color: red'>签到失败：</span></b>\n{e}"
        except WebDriverException as e:
            result += f"<b><span style='color: red'>WebDriver异常：</span></b>\n{e}"
        except Exception as e:
            result += f"<b><span style='color: red'>未知异常：</span></b>\n{e}"

        finally:
            # driver.get('https://bot.sannysoft.com/')
            # total_height = driver.execute_script("return document.body.scrollHeight")
            # driver.set_window_size(1920, total_height)
            # driver.save_screenshot('/tmp/screenshot.png')
            driver.quit()
        return result

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            msg = f"---- 账号({i})V2EX 签到状态 ----\n{self.sign(cookie)}"
            msg_all += msg + "\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("V2EX", [])
    result = V2ex(check_items=_check_items).main()
    send("V2EX", result)
    # print(result)
