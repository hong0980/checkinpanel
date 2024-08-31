# -*- coding: utf-8 -*-
"""
cron: 25 3 0,12 * * *
new Env('恩山论坛 签到');
"""

import re, datetime
from utils import get_data
from notify_mtr import send
from requests_html import HTMLSession

class Enshan:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        url, headers, session, current_date = 'https://www.right.com.cn/forum/home.php', \
        {"Cookie": cookie}, HTMLSession(), datetime.datetime.now().strftime("%Y-%m-%d")
        try:
            params = {'mod': 'spacecp', 'ac': 'credit', 'showcredit': '1'}
            r = session.get(url, headers=headers, params=params)
            name = re.findall(r'访问我的空间">(.*?)</a>', r.text)
            name = name[0] if name else None
            if name is None:
                return (f"<b><span style='color: red'>签到失败</span></b>\n"
                        f"账号({i})无法登录！可能Cookie失效，请重新修改")

            params = {'mod': 'spacecp', 'ac': 'credit'}
            r = session.get(url, headers=headers, params=params)
            today = re.search(rf'<td>{current_date}.*?</td>', r.text)
            color, status = ('green', '成功') if today else ('red', '失败')
            matches = re.findall(r'(恩山币|积分|贡献):\s*</em>(\d+)', r.text)
            points = ''.join([f'{match[0]}: {match[1]}\n' for match in matches])
            return (f'---- {name} 恩山论坛 签到结果 ----\n'
                    f"<b><span style='color: {color}'>签到{status}</span></b>\n\n"
                    f'<b>账户信息</b>\n{points}')

        except Exception:
            import traceback
            return f"<b><span style='color: red'>未知异常：</span></b>\n{traceback.format_exc()}"

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = str(check_item.get("cookie"))
            msg_all += f'{self.sign(cookie, i)}\n\n'
        return msg_all

if __name__ == "__main__":
    result = Enshan(check_items=get_data().get("ENSHAN", [])).main()
    send("恩山论坛 签到", result)
    # print(result)
