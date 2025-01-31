# -*- coding: utf-8 -*-
"""
cron: 3 0 * * *
new Env('ourbits');
"""
import random
import time
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium_stealth import stealth
from utils import get_data

class EnhancedCloudflareBypass:
    def __init__(self, check_items):
        self.check_items = check_items
        self.max_retries = 3  # 最大重试次数
        self.chrome_version = "124.0.6367.78"  # 与实际安装版本一致

    def _create_optimized_driver(self):
        """创建优化稳定性的浏览器实例"""
        options = webdriver.ChromeOptions()
        
        # 内存优化配置
        options.add_argument('--headless=new')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--single-process')  # 单进程模式
        
        # 屏蔽非必要功能
        options.add_argument('--disable-images')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-logging')
        options.add_argument('--disable-notifications')
        
        # 版本伪装
        options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{self.chrome_version} Safari/537.36')
        
        # 实验性参数
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("detach", True)

        service = webdriver.ChromeService(
            executable_path='/usr/bin/chromedriver',
            service_args=[
                '--verbose',
                f'--chrome-version={self.chrome_version}',  # 版本匹配
                '--log-path=/tmp/chromedriver.log'
            ]
        )

        driver = webdriver.Chrome(service=service, options=options)
        
        # 增强型stealth配置
        stealth(driver,
            platform="Win32",
            fix_hairline=True,
            vendor="Google Inc.",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            languages=["zh-CN", "zh"],
            mock_hardware=True,
            run_on_insecure_origins=True,
            hide_webdriver=True  # 强化webdriver隐藏
        )
        return driver

    def _safe_navigate(self, driver, url):
        """带异常处理的智能导航"""
        attempt = 0
        while attempt < self.max_retries:
            try:
                driver.get(url)
                WebDriverWait(driver, 15).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                return True
            except WebDriverException as e:
                print(f"导航异常 [{attempt+1}/{self.max_retries}]: {str(e)}")
                self._recover_session(driver)
                attempt += 1
        return False

    def _recover_session(self, driver):
        """会话恢复机制"""
        try:
            driver.quit()
        except:
            pass
        return self._create_optimized_driver()

    def _solve_cloudflare(self, driver):
        """多阶段验证解决方案"""
        try:
            # 切换到验证框架
            WebDriverWait(driver, 20).until(
                EC.frame_to_be_available_and_switch_to_it(
                    (By.CSS_SELECTOR, "iframe[title*='Cloudflare']")
                )
            )
            
            # 执行验证点击
            checkbox = WebDriverWait(driver, 25).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "label.radio"))
            )
            checkbox.click()
            
            # 等待验证完成
            WebDriverWait(driver, 30).until(
                EC.invisibility_of_element_located((By.ID, "challenge-form"))
            )
            driver.switch_to.default_content()
            return True
        except Exception as e:
            print(f"验证失败: {str(e)}")
            return False

    def sign(self, cookie):
        driver = None
        try:
            driver = self._create_optimized_driver()
            
            # 初始化会话
            if not self._safe_navigate(driver, "https://ourbits.club/login.php"):
                return "初始化失败"
                
            # 注入Cookie
            for c in cookie.split('; '):
                name, value = c.strip().split('=', 1)
                driver.add_cookie({'name': name, 'value': value})
                
            # 访问目标页面并处理验证
            for url in ["https://ourbits.club/torrents.php", 
                       "https://ourbits.club/attendance.php"]:
                if not self._safe_navigate(driver, url):
                    return "导航中断"
                if not self._solve_cloudflare(driver):
                    return "Cloudflare验证失败"
                time.sleep(random.uniform(2,4))
            
            # 执行签到操作
            driver.find_element(By.CSS_SELECTOR, "#signed").click()
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".signed-success"))
            )
            return "签到成功"
            
        except Exception as e:
            traceback.print_exc()
            return f"异常: {str(e)}"
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def main(self):
        results = []
        for index, item in enumerate(self.check_items, 1):
            print(f"正在处理账号 {index}")
            result = self.sign(item.get("cookie"))
            results.append(f"账号{index}: {result}")
            time.sleep(random.randint(5,10))  # 请求间隔防检测
        return "\n".join(results)

if __name__ == "__main__":
    data = get_data()
    check_items = data.get("OURBITS", [])
    bot = EnhancedCloudflareBypass(check_items)
    print(bot.main())