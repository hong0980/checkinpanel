# -*- coding: utf-8 -*-
"""
cron: 10 2 0,9 * * *
new Env('亿破姐 签到');
"""

import re
from time import sleep
from utils import get_data
from notify_mtr import send
from requests_html import HTMLSession

class Get:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(username, password, i):
        s, color, msg, url = HTMLSession(), 'red', '签到失败', 'https://www.ypojie.com'
        try:
            data = {'log': username, 'wp-submit': '登录',
                    'pwd': password, 'rememberme': 'forever',
                    'redirect_to': f'{url}/?cf=1'}
            headers = {'origin': url, 'authority': 'www.ypojie.com'}
            f = s.post(f'{url}/wp-login.php', headers=headers, data=data)
            match = re.search(r'Hi, (\w+)', f.text)
            name = match.group(1) if match else None
            if name is None:
                return (f"<b><span style='color: red'>签到失败</span></b>\n"
                        f"账号{i}登录不成功，用户名或密码可能错误。")

            headers['accept'] = 'application/json'
            p = s.post(f'{url}/wp-admin/admin-ajax.php', headers=headers, data={'action': 'epd_checkin'}).json()
            if isinstance(p, dict):
                color, msg, status = 'green', p.get('msg'), p.get('status')
                if status == 200:
                    msg = '签到成功'
                elif status == 201:
                    color = 'purple'
            sign_msg = f"<b><span style='color: {color}'>{msg}</span></b>"

            r = s.get(f'{url}/vip')
            assets = r.html.find('table.erphpdown-sc-table', first=True).text.replace('\n', '：')
            return (f"---- {name} 亿破姐 签到结果 ----\n"
                    f"{sign_msg}\n{assets}")

        except Exception:
            import traceback
            return f"<b><span style='color: red'>发生错误：</span></b>\n{traceback.format_exc()}"

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            msg = self.sign(check_item.get("username"), check_item.get("password"), i)
            msg_all += f'{msg}\n\n'
        return msg_all

if __name__ == "__main__":
    result = Get(check_items=get_data().get("YPOJIE", [])).main()
    if '签到成功' in result:
        send("亿破姐 签到", result)
    else:
        print(result)
