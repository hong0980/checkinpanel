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
        res = ''
        headers = {
            "Cookie": cookie,
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; WOW64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/102.0.0.0 Safari/537.36"),
        }
        session = requests.session()
        try:
            r = session.get('https://www.right.com.cn/forum/forum.php', headers=headers, timeout=10)
            if r.status_code == 200:
                try:
                    if '退出' in r.text:
                        url = "https://www.right.com.cn/forum/home.php?mod=spacecp&ac=credit&showcredit=1"
                        response = session.get(url, headers=headers, timeout=10)
                        coin = re.findall("恩山币: </em>(.*?) 币 &nbsp", response.text)[0]
                        point = re.findall("<em>积分: </em>(.*?) <span", response.text)[0]
                        res += f"恩山币：{coin}\n积分：{point}"
                    else:
                        res += 'cookie失效'
                except Exception as e:
                    res = f"发生异常: {e}"
            else:
                res += '请求没有响应'
        except requests.RequestException as e:
            res = f"请求发生错误: {e}"
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = str(check_item.get("cookie"))
            msg = f"---- 账号({i})恩山论坛 签到结果 ----\n{self.sign(cookie)}"
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("ENSHAN", [])
    result = Enshan(check_items=_check_items).main()
    send("恩山论坛", result)
    # print(result)
