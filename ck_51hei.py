# -*- coding: utf-8 -*-
"""
cron: 4 0 * * *
new Env('51黑电子论坛 签到');
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
        res = ""
        session = requests.session()
        url = 'http://www.51hei.com/bbs/home.php?mod=spacecp&ac=credit&op=base'
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/102.0.0.0 Safari/537.36",
        }
        try:
            response = session.get(url, headers=headers, timeout=10)
            if '退出' in response.text:
                pattern = r'<em>\s*(黑币|威望|积分|贡献):\s*</em>(\d+)'
                matches = re.findall(pattern, response.text)
                res = ''.join([f'{match[0]}: {match[1]}\n' for match in matches])
            else:
                res = 'cookie失效'

        except Exception as e:
            res = f"发生异常: {e}"
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = str(check_item.get("cookie"))
            msg = f"---- 账号({i})51黑电子论坛 签到结果 ----\n{self.sign(cookie)}"
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("51HEI", [])
    result = nasyun(check_items=_check_items).main()
    send("51黑电子论坛", result)
    # print(result)
