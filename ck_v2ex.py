# -*- coding: utf-8 -*-
"""
cron: 10 12,17 * * *
new Env('V2EX 签到');
"""

import re
from utils import get_data
from notify_mtr import send
from requests_html import HTML, HTMLSession

class V2ex:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        res, msg = '', ''
        headers={
            "Cookie": cookie,
            'authority': 'www.v2ex.com',
        }
        try:
            with HTMLSession(executablePath='/usr/bin/chromium') as s:
                r = s.get('https://www.v2ex.com/mission/daily',  headers=headers)

                if '注册' in r.text:
                    return f'账号({i})无法登录！可能Cookie失效，请重新修改'

                name_element = r.html.find('span[class="bigger"]', first=True)
                msg = f"---- {name_element.text} V2EX 签到状态 ----\n"
                res = f"{msg}<b><span style='color: green'>今天已经签到过了</span></b>"
                headers['referer'] = 'https://www.v2ex.com/mission/daily'
                if '领取 X 铜币' in r.text:
                    href = re.findall(r"(/daily.*?=\d+)", r.text)
                    # href = r.html.search("onclick=\"location.href = '{}';")[0]
                    # <input type="button" class="super normal button" value="查看我的账户余额" onclick="location.href = '/balance';">
                    r = s.get(f'https://www.v2ex.com/mission{href[0]}',  headers=headers)
                    res = f"{msg}<b><span style='color: green'>签到成功</span></b>"
                    r = s.get('https://www.v2ex.com/mission/daily',  headers=headers)

                c = re.findall(r'<div class="cell">(已连续登录 \d+ 天)</div>', r.text)
                p = s.get('https://www.v2ex.com/balance', headers=headers)
                # request_headers = p.request.headers
                # response_headers = p.headers
                # print(request_headers)
                # print(response_headers)
                g = re.findall(r'的(每日登录奖励 \d+ 铜币)', p.text)
                m = p.html.find('a.balance_area', first=True).text.replace(" ", "")
                res += f"\n{c[0]}\n{g[0]}\n当前账户余额：{m} 铜币"

        # except Exception as e:
        #     res = f"{msg}<b><span style='color: red'>未知异常：</span></b>\n{e}"
        finally:
            pass
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            msg = self.sign(cookie, i)
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("V2EX", [])
    result = V2ex(check_items=_check_items).main()
    # send("V2EX", result)
    print(result)
