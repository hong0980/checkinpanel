# -*- coding: utf-8 -*-
"""
cron: 4 0 * * *
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
        res = ""
        session = requests.session()
        url = 'http://www.nasyun.com/home.php?mod=spacecp&ac=credit&op=base'
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/102.0.0.0 Safari/537.36",
        }
        try:
            response = session.get(url, headers=headers, timeout=10)
            if '我的' in response.text
                devote = re.findall("<li><em> 贡献: </em>(.*?) </li>", response.text)[0]
                active = re.findall("<li><em> 活跃: </em>(.*?) </li>", response.text)[0]
                point = re.findall("<em>积分: </em>(.*?) <span", response.text)[0]
                res += f"贡献：{devote}\n活跃：{active}\n积分：{point}"
            else:
                res += 'cookie失效'
        except Exception as e:
            res += f"发生异常: {e}"
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = str(check_item.get("cookie"))
            msg = f"---- 账号({i})那是云签到结果 ----\n{self.sign(cookie)}"
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("NASYUN", [])
    result = nasyun(check_items=_check_items).main()
    send("那是云", result)
    # print(result)
