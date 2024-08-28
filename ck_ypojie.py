# -*- coding: utf-8 -*-
"""
cron: 50 1 0 * * *
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
        s, res, url = HTMLSession(), '', 'https://www.ypojie.com'
        try:
            headers= {'origin': url, 'authority': 'www.ypojie.com'}
            data = {
                'log': username,
                'pwd': password,
                'wp-submit': '登录',
                'rememberme': 'forever',
                'redirect_to': f'{url}/?cf=1',
            }
            f = s.post(f'{url}/wp-login.php', headers=headers, data=data)
            name = f.html.search('> Hi, {} <')
            name = name[0] if name else None
            if name is None:
                return (f"<b><span style='color: red'>签到失败</span></b>\n"
                        f"账号{i}登录不成功，用户名或密码可能错误。")

            r = s.get(f'{url}/vip')
            sign_button = r.html.find('a.usercheck.erphpdown-sc-btn', first=True)

            headers['referer'] = f'{url}/vip'
            headers['accept'] = 'application/json, text/javascript, */*; q=0.01'
            p = s.post(f'{url}/wp-admin/admin-ajax.php', headers=headers, data={'action': 'epd_checkin'})
            color, msg = 'red', '签到失败'
            if 'status' in p.json() and 'msg' in p.json():
                status = p.json().get('status')
                msg = p.json().get('msg')
                if 200 <= status < 210:
                    color = 'green'
                if status == 200 and msg is None:
                    msg = '签到成功'
            sign_msg = f"<b><span style='color: {color}'>{msg}</span></b>"

            r = s.get(f'{url}/vip')
            assets = r.html.search('class="erphpdown-sc-td-title">{}</td> <td>{}</td>')
            res = f"---- {name} 亿破姐 签到结果 ----\n"
            res += f"{sign_msg}\n{assets[0]}： {assets[1]}"

        except Exception as e:
            res = f'发生错误：{str(e)}'
        finally:
            s.close()
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            msg = self.sign(check_item.get("username"), check_item.get("password"), i)
            msg_all += f'{msg}\n\n'
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("YPOJIE", [])
    result = Get(check_items=_check_items).main()
    send("亿破姐 签到", result)
    # print(result)
