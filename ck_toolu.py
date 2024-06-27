# -*- coding: utf-8 -*-
"""
cron: 5 0 * * *
new Env('在线工具');
"""

import re
import requests
from utils import get_data
from notify_mtr import send

class ToolLu:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie):
        headers = {
            "cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/102.0.0.0 Safari/537.36",
        }
        response = requests.get('https://id.tool.lu/sign', headers=headers)
        creditsresponse = requests.get('https://id.tool.lu/credits', headers=headers)
        day = re.findall("你已经连续签到(.*)，再接再厉！", response.text)
        credits= re.findall('<span class="badge bg-warning">(.*)</span>', creditsresponse.text)[0].replace(" ", "")
        if len(day) == 0:
            return "cookie 失效"
        day = day[0].replace(" ", "")
        return f"连续签到 {day}, 当前积分:{credits}"

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            msg = f"---- 账号({i})在线工具签到结果 ----\n{self.sign(cookie)}"
            msg_all += msg + "\n\n"
        return msg_all


if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("TOOLU", [])
    result = ToolLu(check_items=_check_items).main()
    send("在线工具", result)
    # print(result)
