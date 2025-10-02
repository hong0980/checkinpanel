# -*- coding: utf-8 -*-
"""
cron: 10 9,15 * * *
new Env('V2EX 签到');
"""

import re, time, random, shutil, tempfile
from utils import get_data, today, read, write
from notify_mtr import send
from datetime import datetime
from selenium import webdriver
from fake_useragent import UserAgent
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

class V2ex:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def setup_browser(data_dir):
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--headless=new")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"--user-data-dir={data_dir}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        service = webdriver.ChromeService()
        service.executable_path='/usr/bin/chromedriver'
        service.service_args = [
            # '--verbose',                    # 详细日志
            # '--append-log',                 # 如需追加日志
            '--readable-timestamp',         # 可读时间
            '--enable-chrome-logs',         # 启用 Chrome 内部日志
            '--log-path=/tmp/V2ex.log'
        ]

        driver = webdriver.Chrome(options=options, service=service)

        stealth(driver,
            platform="Win32",
            fix_hairline=True,
            hide_webdriver=True,
            vendor="Google Inc.",
            webgl_vendor="Intel Inc.",
            languages=["zh-CN", "zh"],
            renderer="Intel Iris OpenGL Engine",
        )

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
    def sign(cookie, i):
        signKey = f"v2ex_sign_{i}"
        if read(signKey) == today():
            return (f"账号 {i}: ✅ 今日已签到")

        res = ''
        data_dir = tempfile.mkdtemp(prefix="selenium_chrome_")
        driver = V2ex.setup_browser(data_dir)
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
            name_element = driver.find_element(By.CSS_SELECTOR, '.bigger a')
            res = f"----账号 {i} {name_element.text} V2EX 签到状态 ----\n"

            if '领取 X 铜币' in sign_button.get_attribute('value'):
                sign_button.click()
                time.sleep(random.uniform(1.0, 2.0))
                res += f"<b><span style='color: green'>签到成功</span></b>\n"
                write(signKey, today())

            money_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[value='查看我的账户余额']"))
            )
            cell = re.findall(r'>(已连续登录.*?天)<', driver.page_source)[0]
            money_button.click()
            time.sleep(random.uniform(1.0, 2.0))

            formatted_date = datetime.now().strftime('%Y%m%d')
            gray = re.findall(f'{formatted_date}.*?(每日登录奖励.*?)</span>', driver.page_source)
            money = driver.find_element(By.CSS_SELECTOR, "#money .balance_area").text.replace('\n', '').strip()
            res += f"{cell}\n{gray[0]}\n当前账户余额：{money} 铜币"

            with open(f"/tmp/v2ex_{i}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            driver.save_screenshot(f"/tmp/v2ex_{i}.png")

        except TimeoutException as e:
            res = f"{res}<b><span style='color: red'>超时异常：</span></b>\n{e}"
        except NoSuchElementException as e:
            res = f"{res}<b><span style='color: red'>签到失败：</span></b>\n{e}"
        except WebDriverException as e:
            res = f"{res}<b><span style='color: red'>WebDriver异常：</span></b>\n{e}"
        except Exception as e:
            res = f"{res}<b><span style='color: red'>未知异常：</span></b>\n{e}"
        finally:
            driver.quit()
            shutil.rmtree(data_dir, ignore_errors=True)
        return res

    def main(self):
        messages = []
        for i, check_item in enumerate(self.check_items, start=1):
            if i > 1:
                time.sleep(3)
            cookie = check_item.get("cookie")
            messages.append(self.sign(cookie, i))
        return "\n\n".join(messages)

if __name__ == "__main__":
    result = V2ex(check_items=get_data().get("V2EX", [])).main()
    if re.search(r'成功|失败|异常|错误|登录', result):
        send("V2EX 签到", result)
    else:
        print(result)
