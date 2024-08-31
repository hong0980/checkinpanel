# -*- coding: utf-8 -*-
"""
cron: 55 2 0 * * *
new Env('那是云 签到');
"""

import re, datetime
from utils import get_data
from notify_mtr import send
from requests_html import HTMLSession

class NASYUN:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        url, headers = 'http://www.nasyun.com/home.php', {"Cookie": cookie}
        s, current_date = HTMLSession(), datetime.datetime.now().strftime("%Y-%m-%d")
        try:
            r = s.get(url, headers=headers)
            name = re.findall(r'title="访问我的空间" >(\w+)</a></div>', r.text)
            name = name[0] if name else None
            if name is None:
                return (f"<b><span style='color: red'>签到失败</span></b>\n"
                        f"账号({i})无法登录！可能Cookie失效，请重新修改")

            params = {'mod': 'spacecp', 'ac': 'credit', 'op': 'base'}
            f = s.get(url, headers=headers, params=params)

            params.update({'op': 'log', 'suboperation': 'creditrulelog'})
            p = s.get(url, headers=headers, params=params)

            today = re.findall(rf'每天登录.*?(\d+)</td>.*?{current_date}', p.text, re.DOTALL)
            msg = f"<b><span style='color: green'>签到成功</span></b>\n累计登录：{today[0]} 次\n" \
                  if today else "<b><span style='color: red'>签到失败</span></b>\n"

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
    send("那是云 签到", result)
    # print(result)
