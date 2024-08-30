# -*- coding: utf-8 -*-
"""
cron: 25 3 0,12 * * *
new Env('恩山论坛 签到');
"""

from utils import get_data
from notify_mtr import send
import re, requests, datetime

class Enshan:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        res, session = '', requests.session()
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/102.0.0.0 Safari/537.36",
        }
        try:
            r = session.get("https://www.right.com.cn/forum/home.php?mod=spacecp&ac=credit&showcredit=1", headers=headers)
            name = re.findall(r'访问我的空间">(.*?)</a>', r.text)
            name = name[0] if name else None
            if name is None:
                return (f"<b><span style='color: red'>签到失败</span></b>\n"
                        f"账号({i})无法登录！可能Cookie失效，请重新修改")

            r = session.get('https://www.right.com.cn/forum/home.php?mod=spacecp&ac=credit', headers=headers)
            today = re.findall(rf'<td>{datetime.datetime.now().strftime("%Y-%m-%d")}.*?</td>', r.text)
            sign_msg = f"<b><span style='color: red'>签到失败</span></b>" \
                       if not today else "<b><span style='color: green'>签到成功</span></b>"
            pattern = r'(恩山币|积分|贡献):\s*</em>(\d+)'
            matches = re.findall(pattern, r.text)
            res = f"---- {name} 恩山论坛 签到结果 ----\n{sign_msg}\n\n<b>账户信息</b>\n"
            res += ''.join([f'{match[0]}: {match[1]}\n' for match in matches])

        except Exception:
            import traceback
            return f"<b><span style='color: red'>未知异常：</span></b>\n{traceback.format_exc()}"
        return res

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
