# -*- coding: utf-8 -*-
"""
cron: 3 0 * * *
new Env('那是云 签到');
"""
import re
import requests
from utils import get_data
from notify_mtr import send

class nasyun:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie):
        session = requests.session()
        url = 'http://www.nasyun.com/home.php?mod=spacecp&ac=credit&op=base'
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/102.0.0.0 Safari/537.36",
        }
        try:
            r = session.get(url, headers=headers, timeout=10)
            if '立即注册' in r.text:
                return 'cookie失效'
            pattern = r'<em>\s*(云币|贡献|活跃|积分):\s*</em>(\d+)'
            matches = re.findall(pattern, r.text)
            return ''.join([f'{match[0]}: {match[1]}\n' for match in matches])
        except Exception as e:
            return f"发生异常: {e}"

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = str(check_item.get("cookie"))
            msg = f"---- 账号({i}) 那是云 签到结果 ----\n{self.sign(cookie)}"
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("NASYUN", [])
    result = nasyun(check_items=_check_items).main()
    send("那是云", result)
    # print(result)
