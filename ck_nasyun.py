# -*- coding: utf-8 -*-
"""
cron: 55 2 8,16 * * *
new Env('那是云 签到');
"""

import re, datetime
from notify_mtr import send
from requests_html import HTMLSession
from utils import get_data, store

class NASYUN:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        signKey = f"nasyun_sign_{i}"
        if store.has_signed(signKey):
            return (f"账号 {i}: ✅ 今日已签到")

        url, headers = 'http://www.nasyun.com/home.php', {"Cookie": cookie}
        s, current_date = HTMLSession(), datetime.datetime.now().strftime("%Y-%m-%d")
        sign_msg = "<b><span style='color: red'>签到失败</span></b>\n"
        try:
            r = s.get(url, headers=headers)
            name = re.findall(r'title="访问我的空间" >(\w+)</a></div>', r.text)
            name = name[0] if name else None
            if name is None:
                return f"{sign_msg}账号({i})无法登录！可能Cookie失效，请重新修改"

            params = {'mod': 'spacecp', 'ac': 'credit', 'op': 'base'}
            f = s.get(url, params=params, headers=headers)

            params.update({'op': 'log', 'suboperation': 'creditrulelog'})
            p = s.get(url, params=params, headers=headers)

            todays = re.findall(rf'每天登录.*?(\d+)</td>.*?{current_date}', p.text, re.DOTALL)
            msg = f"<b><span style='color: green'>签到成功</span></b>\n累计登录：{todays[0]} 次\n" \
                  if todays else sign_msg
            if todays:
                store.mark_signed(signKey)

            matches = re.findall(r'(云币|贡献|活跃|积分):\s*</em>(\d+)', f.text)
            res = f"---- {name} 那是云 签到结果 ----\n{msg}\n<b>账户信息</b>\n"
            res += ''.join([f'{match[0]}: {match[1]}\n' for match in matches])

        except Exception:
            import traceback
            return f"<b><span style='color: red'>发生异常：</span></b>\n{traceback.format_exc()}"
        return res

    def main(self):
        msg_all = ''
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = str(check_item.get("cookie"))
            msg_all += f'{self.sign(cookie, i)}\n\n'
        return msg_all

if __name__ == "__main__":
    result = NASYUN(check_items=get_data().get("NASYUN", [])).main()
    if '成功' in result or '失败' in result:
        send("那是云 签到", result)
    else:
        print(result)
