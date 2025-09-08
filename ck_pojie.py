# -*- coding: utf-8 -*-
"""
cron: 53 11 * * *
new Env('吾爱破解');
"""

from utils import get_data
import re, time, random
from notify_mtr import send
from datetime import datetime
from selenium import webdriver
from fake_useragent import UserAgent
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

class Pojie:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def setup_browser():
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        driver = webdriver.Chrome(
            options=options,
            service=Service('/usr/bin/chromedriver')
        )

        evasions = [
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
            "Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN','zh','en']})",
            "Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]})",
            "Object.defineProperty(navigator, 'platform', {get: () => 'Win32'})",
        ]
        for script in evasions:
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": script})

        headers = {
            "User-Agent": UserAgent().chrome,
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        try:
            driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": headers})
        except Exception:
            pass

        return driver

    @staticmethod
    def sign(cookie):
        res, msg = '', ''
        driver = Pojie.setup_browser()

        try:
            driver.get('https://www.52pojie.cn/forum.php')
            for single_cookie in cookie.split('; '):
                name, value = single_cookie.split('=', 1)
                driver.add_cookie({ 'name': name, 'value': value })

            driver.get('https://www.52pojie.cn/forum.php')
            print(driver.page_source)

        except TimeoutException as e:
            res = f"{msg}<b><span style='color: red'>超时异常：</span></b>\n{e}"
        except NoSuchElementException as e:
            res = f"{msg}<b><span style='color: red'>签到失败：</span></b>\n{e}"
        except WebDriverException as e:
            res = f"{msg}<b><span style='color: red'>WebDriver异常：</span></b>\n{e}"
        except Exception as e:
            res = f"{msg}<b><span style='color: red'>未知异常：</span></b>\n{e}"
        finally:
            driver.quit()
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            sign_msg = self.sign(cookie)
            msg = f"账号 {i} 签到状态: {sign_msg}"
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("POJIE", [])
    result = Pojie(check_items=_check_items).main()
    # send("吾爱破解", result)
    print(result)
