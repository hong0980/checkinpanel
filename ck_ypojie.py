# -*- coding: utf-8 -*-
"""
cron: 1 0 * * *
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
        res = ''
        try:
            with HTMLSession(executablePath='/usr/bin/chromium') as s:
                res = ''
                headers= {
                    'authority': 'www.ypojie.com',
                    'origin': 'https://www.ypojie.com',
                    # 'cookie': 'wordpress_test_cookie=WP%20Cookie%20check',
                }

                data = {
                    'log': username,
                    'pwd': password,
                    'wp-submit': '登录',
                    'rememberme': 'forever',
                    'redirect_to': 'https://www.ypojie.com/?cf=1',
                    # 'testcookie': '1',
                }

                p = s.post('https://www.ypojie.com/wp-login.php', headers=headers, data=data)

                if '登录 ‹ 易破解' in p.text:
                    return f'账号{i}登录不成功，用户名或密码可能错误。'

                r = s.get('https://www.ypojie.com/vip')
                name = r.html.search('> Hi, {} <')
                res = f"---- {name[0]} 亿破姐 签到结果 ----\n"
                assets = r.html.search('class="erphpdown-sc-td-title">{}</td> <td>{}</td>')
                # <a href="javascript:;" class="usercheck erphpdown-sc-btn active">已签到</a>
                # <a href="javascript:;" class="usercheck erphpdown-sc-btn erphp-checkin">今日签到</a>
                # <a href="javascript:;" class="usercheck erphpdown-sc-btn erphp-checkin disabled active">签到成功</a>
                sign_button = r.html.find('a.usercheck.erphpdown-sc-btn', first=True)

                if '已签到' in sign_button.text:
                    res += f"<b><span style='color: green'>今天已经签到</span></b>\n{assets[0]}： {assets[1]}"
                    return res

                headers['referer'] = 'https://www.ypojie.com/vip'
                headers['accept'] = 'application/json, text/javascript, */*; q=0.01'
                r = s.post('https://www.ypojie.com/wp-admin/admin-ajax.php', headers=headers, data={'action': 'epd_checkin'})
                sign_button = r.html.find('a.usercheck.erphpdown-sc-btn', first=True)

                if '签到成功' in sign_button.text:
                    res += f"<b><span style='color: green'>签到成功</span></b>\n{assets[0]}： {assets[1]}"

        finally:
            pass
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            username = check_item.get("username")
            password = check_item.get("password")
            msg = self.sign(username, password, i)
            msg_all += f'{msg}\n\n'
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("YPOJIE", [])
    result = Get(check_items=_check_items).main()
    # send("亿破姐", result)
    print(result)
