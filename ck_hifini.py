# -*- coding: utf-8 -*-
"""
cron: 0 0 0 * * *
new Env('HiFiNi 签到');
"""

import re
from utils import get_data
from notify_mtr import send
from requests_html import HTMLSession

class HiFiNi:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookies, i):
        s = HTMLSession()
        url = "https://www.hifini.com/sg_sign.htm"
        headers = {'cookie': cookies}
        r = s.get(url, headers=headers)
        name = r.html.find('li.username', first=True)
        if name is None:
            return (f"<b><span style='color: red'>签到失败</span></b>\n"
                    f"账号({i})无法登录！可能Cookie失效，请重新修改")

        sign = re.findall(r'sign = "(\w+)"', r.text)
        headers['x-requested-with'] = 'XMLHttpRequest'
        p = s.post(url, data={'sign': sign[0]}, headers=headers).json()
        day, code, message = '', p.get('code'), p.get('message')
        if code == '-1':
            r = s.get(url, headers=headers)
            day = '\n已经' + re.findall(r'(连续签到 \d+ 天)', r.text)[0]
        return f"--- {name.text} HiFiNi 签到结果 ---\n{message}{day}"

    def main(self):
        msg_all = ''
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            msg_all += f'{self.sign(cookie, i)}\n\n'
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("HIFINI", [])
    result = HiFiNi(check_items=_check_items).main()
    send("HiFiNi 签到", result)
    # print(result)
