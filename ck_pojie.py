# -*- coding: utf-8 -*-
"""
cron: 53 11 * * *
new Env('吾爱破解');
"""
from time import sleep
import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from notify_mtr import send
from utils import get_data


class Pojie:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie):
        from selenium import webdriver
        from selenium_stealth import stealth
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, WebDriverException

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # 无头模式
        options.add_argument('--no-sandbox')  # 禁用沙箱
        options.add_argument("start-maximized")  # 最大化窗口
        options.add_argument('--disable-dev-shm-usage')  # 禁用/dev/shm
        options.add_argument('--disable-blink-features=AutomationControlled')  # 禁用自动化控制特征
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-infobars')  # 禁用信息条
        options.add_argument('--disable-gpu')  # 禁用GPU
        options.add_argument('--disable-software-rasterizer')  # 禁用软件光栅化
        options.add_argument('--mute-audio')  # 静音

        service = webdriver.ChromeService(
            log_output='/tmp/52pojie.txt',
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

        # 注入JavaScript来模拟真实浏览器环境
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
          "source": """
                // 禁用WebDriver标志
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                });

                // 模拟Navigator对象
                Object.defineProperty(navigator, 'plugins', {
                  get: () => [1, 2, 3, 4, 5],
                });
                Object.defineProperty(navigator, 'mimeTypes', {
                  get: () => [1, 2, 3, 4, 5],
                });

                // 模拟WebGL和Canvas指纹
                const originalWebGLRenderingContext = WebGLRenderingContext;
                WebGLRenderingContext = function() {
                  const renderingContext = new originalWebGLRenderingContext();
                  // 这里可以添加更多模拟WebGL的方法
                  return renderingContext;
                };
                const originalCanvas = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function() {
                  if (arguments[0].toLowerCase() === 'webgl') {
                    return new WebGLRenderingContext();
                  }
                  return originalCanvas.apply(this, arguments);
                };

                // 模拟屏幕分辨率和窗口大小
                window.matchMedia = window.matchMedia || function() {
                  return {
                    matches: false,
                    addListener: function() {},
                    removeListener: function() {}
                  };
                };

                // 模拟UserAgent
                const originalUserAgent = navigator.userAgent;
                Object.defineProperty(navigator, 'userAgent', {
                  get: () => originalUserAgent.replace(/HeadlessChrome/, 'Chrome'),
                });

                // 模拟Languages
                const originalLanguages = navigator.languages;
                Object.defineProperty(navigator, 'languages', {
                  get: () => originalLanguages,
                });

                // 模拟Permissions
                const originalPermissions = navigator.permissions;
                Object.defineProperty(navigator, 'permissions', {
                  get: () => originalPermissions,
                });

                // 模拟Geolocation
                const originalGeolocation = navigator.geolocation;
                Object.defineProperty(navigator, 'geolocation', {
                  get: () => originalGeolocation,
                });

                // 模拟Storage
                const originalStorage = window.localStorage;
                Object.defineProperty(window, 'localStorage', {
                  get: () => originalStorage,
                });

                // 模拟Runtime
                const originalRuntime = window.chrome.runtime;
                Object.defineProperty(window.chrome, 'runtime', {
                  get: () => originalRuntime,
                });

                // 模拟App
                const originalApp = window.chrome.app;
                Object.defineProperty(window.chrome, 'app', {
                  get: () => originalApp,
                });

                // 模拟Extensions
                const originalExtensions = window.chrome.extensions;
                Object.defineProperty(window.chrome, 'extensions', {
                  get: () => originalExtensions,
                });
          """
        })
        try:
            result = ''
            url = 'https://www.52pojie.cn/forum.php'
            driver.get(url)

            for single_cookie in cookie.split('; '):
                name, value = single_cookie.split('=', 1)
                driver.add_cookie({'name': name, 'value': value})
            sleep(2)
            driver.get(url)
            # 找到登录按钮并点击
            login_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="um"]/p[2]/a[1]')))
            login_button.click()
            for i in range(5):
                screenshot_name = f'/tmp/图片_52Pojie_{i}.png'
                source_code_name = f'/tmp/52Pojie_{i}.html.txt'
                driver.save_screenshot(screenshot_name)
                with open(source_code_name, 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                sleep(1)

            # if '我的资产' in driver.page_source:

            # else:
            #     result = '用户名或密码出错，不能登录'
        except TimeoutException as e:
            result = f"等待元素出现超时：{e}"
            # 处理超时异常的代码
        except ElementNotInteractableException as e:
            result = f"元素不可交互：{e}"
        except NoSuchElementException as e:
            result = "未找到元素："
        except Exception as e:
            result = f"发生其他异常：{e}"
        finally:
            driver.quit()
        return result

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
