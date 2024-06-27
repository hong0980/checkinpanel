# -*- coding: utf-8 -*-
"""
cron: 3 0 * * *
new Env('ourbits');
"""
from time import sleep
from utils import get_data
from notify_mtr import send
import logging

# 设置日志记录器
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

class Get:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie):
        import traceback
        from selenium import webdriver
        from selenium_stealth import stealth
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, WebDriverException
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.action_chains import ActionChains

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument("start-maximized")
        options.add_argument("--enable-javascript")
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        service = webdriver.ChromeService(
            log_output='/tmp/ourbits_service.log',
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
            res = ""
            url = 'https://ourbits.club/torrents.php'
            daily_url = 'https://ourbits.club/attendance.php'
            driver.get(url)

            for single_cookie in cookie.split('; '):
                name, value = single_cookie.split('=', 1)
                driver.add_cookie({'name': name, 'value': value})
            sleep(2)
            driver.get(url)

            if "欢迎回来" in driver.page_source:
                if '签到得魔力' in driver.page_source:
                    try:
                        driver.find_element(By.CSS_SELECTOR, '#info_block .faqlink').click()
                        # driver.get(daily_url)
                        # 每隔一秒保存截图和网页源代码
                        for i in range(5):
                            screenshot_name = f'/tmp/图片_Pojie_{i}.png'
                            source_code_name = f'/tmp/Pojie_{i}.html.txt'
                            driver.save_screenshot(screenshot_name)
                            with open(source_code_name, 'w', encoding='utf-8') as f:
                                f.write(driver.page_source)
                            sleep(1)
                        WebDriverWait(driver, 300).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'cf-turnstile'))
                        )
                    except TimeoutException as e:
                        logger.error("等待元素出现超时：", exc_info=True)
                        # 处理超时异常的代码
                    except ElementNotInteractableException as e:
                        logger.error("元素不可交互：", exc_info=True)
                        # 处理元素不可交互异常的代码
                    except NoSuchElementException as e:
                        logger.error("未找到元素：", exc_info=True)
                        # 处理未找到元素异常的代码
                    except Exception as e:
                        logger.error("发生其他异常：", exc_info=True)
                elif "抱歉" in driver.page_source:
                    res += message
            else:
                res += 'cookie 失效'
            return res

        finally:
            # driver.get('https://bot.sannysoft.com/')
            # total_height = driver.execute_script("return document.body.scrollHeight")
            # driver.set_window_size(1920, total_height)
            # driver.save_screenshot('/tmp/sannysoft.png')
            driver.quit()

        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            msg = f"---- 账号({i})ourbits签到结果 ----\n{self.sign(cookie)}"
            msg_all += msg + "\n\n"

        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("OURBITS", [])
    result = Get(check_items=_check_items).main()
    # send("ourbits", result)
    print(result)
