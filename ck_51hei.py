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
                xi1 = re.findall("<em> 黑币: </em>(.*?) &nbsp;", response.text)[0]
                devote = re.findall("<li><em> 威望: </em>(.*?) </li>", response.text)[0]
                active = re.findall("<li><em> 贡献: </em>(.*?) </li>", response.text)[0]
                point = re.findall("<em>积分: </em>(.*?) <span", response.text)[0]
                res += f"黑币：{xi1}\n积分：{point}\n威望：{devote}\n贡献：{active}"
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
