# -*- coding: utf-8 -*-
"""
cron: 3 0 * * *
new Env('智能电视网 签到');
"""
import re
from time import sleep
from utils import get_data
from notify_mtr import send
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

class znds:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # 无头模式
        options.add_argument('--no-sandbox')
        options.add_argument("start-maximized")
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        service = webdriver.ChromeService(
            log_output='/tmp/znds.log',
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
            result = ''
            driver.get('https://www.znds.com//')
            for single_cookie in cookie.split('; '):
                name, value = single_cookie.split('=', 1)
                driver.add_cookie({'name': name, 'value': value})
            driver.refresh()
            sleep(3)

            if '立即注册' in driver.page_source:
                return '<b><span style="color: red">无法登录！可能Cookie失效，请重新修改</span></b>'

            if '打卡签到' in driver.page_source:
                sign_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="toptb"]/div/div[2]/a[2]/font'))
                )
                sign_button.click()
                alert_info = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'alert_info'))
                )
                result = f"<b><span style='color: green'>签到成功</span></b>\n{alert_info.text}\n"
            else:
                result = f"<b><span style='color: green'>今天已经签到过了</span></b>\n"

            try:
                driver.get('https://www.znds.com/home.php?mod=spacecp&ac=credit')
                pattern = r'<em>\s*(金币|积分|威望|Z币):\s*</em>(\d+)'
                matches = re.findall(pattern, driver.page_source)
                result += ''.join([f'{match[0]}: {match[1]}\n' for match in matches])
            except NoSuchElementException as e:
                result += f"<b><span style='color: red'>获取积分信息失败：</span></b>\n{e}"
            except Exception as e:
                result += f"<b><span style='color: red'>获取积分信息未知异常：</span></b>\n{e}"

        except TimeoutException as e:
            result = f"<b><span style='color: red'>超时异常：</span></b>\n{e}"
        except NoSuchElementException as e:
            result = f"<b><span style='color: red'>签到失败：</span></b>\n{e}"
        except WebDriverException as e:
            result = f"<b><span style='color: red'>WebDriver异常：</span></b>\n{e}"
        except Exception as e:
            result = f"<b><span style='color: red'>未知异常：</span></b>\n{e}"

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
            msg = f"---- 账号({i}) 智能电视网 签到结果 ----\n{self.sign(cookie)}"
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("ZNDS", [])
    result = znds(check_items=_check_items).main()
    send("智能电视网", result)
    # print(result)
