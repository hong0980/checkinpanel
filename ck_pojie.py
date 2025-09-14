"""
cron: 53 11 * * *
new Env('吾爱破解');
"""

from utils import get_data
import re, time, random, shutil, tempfile
from notify_mtr import send
from datetime import datetime
from selenium import webdriver
from fake_useragent import UserAgent
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

def setup_browser():
    user_data_dir = tempfile.mkdtemp(prefix="selenium_chrome_")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument(f"--user-agent={UserAgent().chrome}")
    options.add_argument("--disable-gpu")  # 新增：解决 GPU 初始化错误
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    service = webdriver.ChromeService()
    service.executable_path='/usr/bin/chromedriver'
    service.service_args = [
        '--verbose',                    # 详细日志
        '--readable-timestamp',         # 可读时间
        '--enable-chrome-logs',         # 启用 Chrome 内部日志
        '--no-sandbox',                 # 容器中常用
        '--disable-dev-shm-usage',      # 防止内存溢出
        # '--append-log',               # 如需追加日志
        '--log-path=/tmp/52pojie.log'
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
    actions = ActionChains(driver)
    actions.move_by_offset(random.randint(10, 100), random.randint(10, 100)).perform()

    # 禁用 debugger 语句
    driver.execute_script("""
        (function() {
            window.__proto__.__defineGetter__('debugger', () => {});
            Object.defineProperty(window, 'debugger', {value: undefined, writable: false});
            let originalSetInterval = window.setInterval;
            window.setInterval = function(callback, timeout) {
                if (typeof callback === 'function' && callback.toString().includes('debugger')) return;
                if (typeof callback === 'string' && callback.includes('debugger')) return;
                return originalSetInterval.apply(this, arguments);
            };
            let originalSetTimeout = window.setTimeout;
            window.setTimeout = function(callback, timeout) {
                if (typeof callback === 'function' && callback.toString().includes('debugger')) return;
                if (typeof callback === 'string' && callback.includes('debugger')) return;
                return originalSetTimeout.apply(this, arguments);
            };
        })();
    """)

    return driver, user_data_dir

def sign(cookie, i):
    msg = ''
    driver, user_data_dir = setup_browser()

    try:
        driver.get('https://www.52pojie.cn/forum.php')
        for single_cookie in cookie.split('; '):
            name, value = single_cookie.split('=', 1)
            driver.add_cookie({'name': name, 'value': value})
        time.sleep(2)

        driver.get('https://www.52pojie.cn/forum.php')
        # driver.get('https://visit.zjsru.edu.cn/visitor/qrCode?id=fec1f2b23ce1f0bb1a595423af169b79')


        if '自动登录' in driver.page_source:
            return f'❌ 无法登录！可能Cookie失效，请重新修改'

        name_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'strong.vwmy a[href*="uid="]'))
        )
        um_element = driver.find_element(By.CSS_SELECTOR, '#um p:nth-of-type(2)')
        msg = f"---- {name_element.text} 吾爱破解 签到状态 ----\n"
        upmine = driver.find_element(By.ID, "g_upmine").get_attribute("textContent").strip()
        integral = driver.find_element(By.ID, "extcreditmenu").get_attribute("textContent").strip()

        if len(driver.find_elements(By.CSS_SELECTOR, 'img.qq_bind[src*="wbs.png"]')) > 0:
            return f"{msg}<b><span style='color: green'>✅ 今天已经签到过了</span></b>\n{integral} | {upmine}"

        try:
            sign_button = driver.find_element(By.CSS_SELECTOR, 'img.qq_bind[src*="qds.png"]')
            driver.execute_script("arguments[0].scrollIntoView();arguments[0].click()", sign_button)
            time.sleep(8)
            if len(driver.find_elements(By.CSS_SELECTOR, 'img.qq_bind[src*="wbs.png"]')) > 0:
                return f"{msg}✅ 签到成功\n{integral} | {upmine}"
        except NoSuchElementException:
            return f"{msg}\n❌ 签到失败"

    except TimeoutException as e:
        return f"{msg}<b><span style='color: red'>超时异常：</span></b>\n{e}"
    except NoSuchElementException as e:
        return f"{msg}<b><span style='color: red'>签到失败：</span></b>\n{e}"
    except WebDriverException as e:
        return f"{msg}<b><span style='color: red'>WebDriver异常：</span></b>\n{e}"
    except Exception as e:
        return f"{msg}<b><span style='color: red'>未知异常：</span></b>\n{e}"
    finally:
        try:
            with open(f"/tmp/52pojie_{i}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            driver.save_screenshot(f"/tmp/52pojie_{i}.png")
        except:
            pass
        driver.quit()
        shutil.rmtree(user_data_dir, ignore_errors=True)

def main():
    _data = get_data()
    check_items = _data.get("POJIE", [])

    msg_all = ""
    for i, check_item in enumerate(check_items, start=1):
        cookie = check_item.get("cookie")
        sign_msg = sign(cookie, i)
        msg = f"账号 {i} 签到状态: {sign_msg}"
        msg_all += msg + "\n\n"

    return msg_all

if __name__ == "__main__":
    result = main()
    # send("吾爱破解", result)
    print(result)
