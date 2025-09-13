# -*- coding: utf-8 -*-
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
        user_data_dir = tempfile.mkdtemp(prefix="selenium_chrome_")
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument("--headless")
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

        return driver, user_data_dir

    @staticmethod
    def sign(cookie):
        res, msg = '', ''
        driver, user_data_dir = Pojie.setup_browser()

        try:
            driver.get('https://www.52pojie.cn/forum.php')
            for single_cookie in cookie.split('; '):
                name, value = single_cookie.split('=', 1)
                driver.add_cookie({ 'name': name, 'value': value })

            driver.get('https://www.52pojie.cn/forum.php')
           #  print(driver.page_source)

           #  <p> 已经签到页面
           #  <a href="home.php?mod=task&amp;do=apply&amp;id=2&amp;referer=%2Fforum.php"><img src="https://static.52pojie.cn/static/image/common/qds.png" class="qq_bind" align="absmiddle" alt=""></a> <span class="pipe">|</span><a href="home.php?mod=spacecp&amp;ac=credit&amp;showcredit=1" id="extcreditmenu" onmouseover="delayShow(this, showCreditmenu);" class="showmenu">积分: 11</a>
           #  <span class="pipe">|</span><a href="home.php?mod=spacecp&amp;ac=usergroup" id="g_upmine" class="showmenu" onmouseover="delayShow(this, showUpgradeinfo)">用户组: 锋芒初露</a>
           #  </p>

           #  <p> 没有签到页面
           #  <a href="javascript:void(0);"><img src="https://www.52pojie.cn/static/image/common/wbs.png" class="qq_bind" align="absmiddle" alt=""></a> <span class="pipe">|</span><a href="home.php?mod=spacecp&amp;ac=credit&amp;showcredit=1" id="extcreditmenu" onmouseover="delayShow(this, showCreditmenu);" class="showmenu">积分: 11</a>
           #  <span class="pipe">|</span><a href="home.php?mod=spacecp&amp;ac=usergroup" id="g_upmine" class="showmenu" onmouseover="delayShow(this, showUpgradeinfo)">用户组: 锋芒初露</a>
           #  </p>

           #  <div id="um">
           #  <div class="avt y"><a href="home.php?mod=space&amp;uid=720462"><img src="https://avatar.52pojie.cn/data/avatar/000/72/04/62_avatar_small.jpg" onerror="this.onerror=null;this.src='https://avatar.52pojie.cn/images/noavatar_small.gif'"></a></div>
           #  <p>
           #  <strong class="vwmy qq"><a href="home.php?mod=space&amp;uid=720462" target="_blank" title="访问我的空间">hong0980</a></strong>
           #  <span class="pipe">|</span><a href="home.php?mod=space&amp;do=reward&amp;view=me" id="rewards" class="showmenu a" onmouseover="showMenu({'ctrlid':'rewards'})"><em class="showtipex"></em>悬赏</a><span class="pipe">|</span><a href="javascript:;" id="myitem" class="showmenu" onmouseover="showMenu({'ctrlid':'myitem'});">我的</a>
           #  <span class="pipe">|</span><a href="home.php?mod=spacecp">设置</a>
           #  <span class="pipe">|</span><a href="home.php?mod=space&amp;do=pm" id="pm_ntc">消息</a>
           #  <span class="pipe">|</span><a href="home.php?mod=space&amp;do=notice" id="myprompt" class="a showmenu" onmouseover="showMenu({'ctrlid':'myprompt'});">提醒</a><span id="myprompt_check"></span>
           #  <span class="pipe">|</span><a href="member.php?mod=logging&amp;action=logout&amp;formhash=700e89be">退出</a>
           #  </p>
           #  <p>
           #  <img src="https://static.52pojie.cn/static/image/common/wbs.png" class="qq_bind" align="absmiddle" alt=""> <span class="pipe">|</span><a href="home.php?mod=spacecp&amp;ac=credit&amp;showcredit=1" id="extcreditmenu" onmouseover="delayShow(this, showCreditmenu);" class="showmenu">积分: 12</a>
           #  <span class="pipe">|</span><a href="home.php?mod=spacecp&amp;ac=usergroup" id="g_upmine" class="showmenu" onmouseover="delayShow(this, showUpgradeinfo)">用户组: 锋芒初露</a>
           #  </p>
           #  </div>

           #  # 等待页面加载完成，确保 #um 存在
           #  um_element = WebDriverWait(driver, 10).until(
           #      EC.presence_of_element_located((By.ID, "um"))
           #  )
           #  html_content = um_element.get_attribute('innerHTML')

           #  # 执行签到函数
           #  driver.execute_script(
           #      """
           #      function qianDao() {
           #          if (location.pathname === '/home.php' && location.search.indexOf('mod=task') > -1) {
           #              return;
           #          }
           #          let qiandao = document.querySelector('#um a[href^="home.php?mod=task&do=apply&id=2"]');
           #          if (qiandao) {
           #              let iframe = document.createElement('iframe');
           #              document.lastElementChild.appendChild(iframe);
           #              iframe.style = 'display: none;';
           #              iframe.src = qiandao.href;
           #              let img = qiandao.querySelector('.qq_bind');
           #              if (img) {
           #                  img.src = 'https://www.52pojie.cn/static/image/common/wbs.png';
           #              }
           #              qiandao.href = 'javascript:void(0);';
           #          }
           #      }
           #      qianDao();
           #      """
           #  )
           #  time.sleep(3)

           # # 判断结果
           #  try:
           #      um_element.find_element(By.XPATH, './/img[contains(@src, "wbs.png")]')
           #      res = "✅ 签到成功"
           #  except NoSuchElementException:
           #      try:
           #          um_element.find_element(By.XPATH, './/img[contains(@src, "qds.png")]')
           #          res = "🟡 签到失败"
           #      except NoSuchElementException:
           #          res = "无签到任务"

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
            shutil.rmtree(user_data_dir, ignore_errors=True)
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
