# -*- coding: utf-8 -*-
"""
cron: 10 9,15 * * *
new Env('V2EX 签到');
"""

import re, urllib3
from utils import get_data
from notify_mtr import send
from datetime import datetime
from requests_html import HTML, HTMLSession
urllib3.disable_warnings()

class V2ex:
    def __init__(self, check_items):
        self.check_items = check_items
        self.url = "https://www.v2ex.com/mission/daily"

    def sign(self, cookie, proxy, i):
        res = ''
        try:
            s = HTMLSession()
            s.headers.update({
                "referer": self.url,
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
                "accept": "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/webp,image/apng,*/*;"
                "q=0.8,application/signed-exchange;v=b3;q=0.9",
            })
            s.cookies.update({
                item.split("=")[0]: item.split("=", 1)[1]
                for item in cookie.split("; ")
            })
            if proxy:
                s.proxies.update({"http": proxy, "https": proxy})

            r = s.get(self.url, verify=False)
            urls = r.html.search('onclick="location.href = \'{}\';" />')
            url = urls[0] if urls else None
            if url is None:
                return f'账号({i})无法登录！可能Cookie失效，请重新修改'

            sign_msg = f"<b><span style='color: green'>今天已经签到过了</span></b>"
            if 'once' in url:
                s.get(f'https://www.v2ex.com{url}', verify=False)
                sign_msg = f"<b><span style='color: green'>签到成功</span></b>"
                r = s.get(self.url, verify=False)
            username = r.html.find('span[class="bigger"]', first=True)
            datas = re.findall(r'<div class="cell">(已连续登录 \d+ 天)</div>', r.text)

            p = s.get('https://www.v2ex.com/balance')
            today = re.findall(rf'{datetime.now().strftime("%Y%m%d")}.*?(每日登录奖励 \d+ 铜币)</span>', p.text)
            sign_msg = f"<b><span style='color: red'>签到失败</span></b>" if not today[0] else sign_msg
            total = p.html.find('a.balance_area', first=True).text.replace(" ", "")
            credit_info = f"{datas[0]}\n{today[0]}\n当前账户余额：{total} 铜币"

            res = (f"---- {username.text} V2EX 签到状态 ----"
                   f'\n{sign_msg}\n{credit_info}')

        except Exception as e:
            res = f"<b><span style='color: red'>未知异常：</span></b>\n{e}"
        finally:
            pass
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            proxy = check_item.get("proxy", "")
            cookie = check_item.get("cookie")
            msg_all += f'{self.sign(cookie, proxy, i)}\n\n'
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("V2EX", [])
    result = V2ex(check_items=_check_items).main()
    send("V2EX 签到", result)
    # print(result)
