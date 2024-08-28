# -*- coding: utf-8 -*-
"""
cron: 10 9,15 * * *
new Env('V2EX 签到');
"""

import re
from utils import get_data
from notify_mtr import send
from datetime import datetime
from requests_html import HTMLSession

class V2ex:
    def __init__(self, check_items):
        self.check_items = check_items
        self.url = "https://www.v2ex.com/mission/daily"

    def sign(self, cookie, proxy, i):
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

            r = s.get(self.url)
            urls = r.html.search('onclick="location.href = \'{}\';"')
            url = urls[0] if urls else None
            if url is None:
                return (f"<b><span style='color: red'>签到失败</span></b>\n"
                        f"账号({i})无法登录！可能Cookie失效，请重新修改")

            sign_msg = f"<b><span style='color: orange'>今天已经签到过了</span></b>"
            if 'once' in url:
                r = s.get(f'https://www.v2ex.com{url}')
                sign_msg = f"<b><span style='color: green'>签到成功</span></b>"
            username = r.html.find('span.bigger', first=True)
            datas = re.findall(r'>(已连续登录 \d+ 天)<', r.text)

            p = s.get('https://www.v2ex.com/balance')
            today = re.findall(rf'{datetime.now().strftime("%Y%m%d")}.*?(每日登录奖励 \d+ 铜币)</span>', p.text)
            total = p.html.find('table.data tr:nth-of-type(2) td:nth-of-type(4)', first=True)
            sign_msg, today = (sign_msg, today[0] + '\n') if today else \
                              (f"<b><span style='color: red'>签到失败</span></b>", '')

            return (f'---- {username.text} V2EX 签到状态 ----\n{sign_msg}\n'
                    f"{datas[0]}\n{today}当前账户余额：{total.text} 铜币")

        except Exception:
            import traceback
            return f"<b><span style='color: red'>未知异常：</span></b>\n{traceback.format_exc()}"

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
