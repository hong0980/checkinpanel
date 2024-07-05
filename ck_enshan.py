# -*- coding: utf-8 -*-
"""
cron: 2 0 * * *
new Env('恩山论坛');
"""

import re
import requests
from utils import get_data
from notify_mtr import send

class Enshan:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie):
        res = ""
        session = requests.session()
        u = "https://www.right.com.cn/forum/home.php?mod=spacecp&ac=credit&showcredit=1"
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/102.0.0.0 Safari/537.36",
        }
        try:
            r = session.get(u, headers=headers, timeout=10)
            if '退出' in r.text:
                pattern = r'<em>\s*(恩山币|积分|贡献):\s*</em>(\d+)'
                matches = re.findall(pattern, r.text)
                res = ''.join([f'{match[0]}: {match[1]}\n' for match in matches])
            else:
                res = 'cookie失效'

        except Exception as e:
            res = f"发生异常: {e}"
        except requests.RequestException as e:
            res = f"请求发生错误: {e}"
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = str(check_item.get("cookie"))
            msg = f"---- 账号({i})恩山论坛 签到结果 ----\n{self.sign(cookie)}"
            msg_all += msg + "\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("ENSHAN", [])
    result = Enshan(check_items=_check_items).main()
    send("恩山论坛", result)
    # print(result)
