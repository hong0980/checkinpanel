# -*- coding: utf-8 -*-
"""
cron: 5 0 * * *
new Env('nicept');
"""

import re
import requests
from notify_mtr import send
from utils import get_data

class nicept:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie):
        res = ""
        url = 'https://www.nicept.net/attendance.php'
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/102.0.0.0 Safari/537.36",
        }
        response = requests.post(url, headers=headers)

        if "登錄" in response.text:
            return 'cookie 失效'

        if "簽到成功" in response.text:
            pattern = r'第 <b>(\d+)</b>.*?<b>(\d+)</b>.*?<b>(\d+)</b>.*?值'
            result = re.findall(pattern, response.text)[0]
            res += f'pthome 签到成功\n这是您的第{result[0]}次签到，已连续签到{result[1]}天，本次签到获得{result[2]}个魔力值。'
        else:
            res += "签到失败"
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            msg = f"---- 账号({i})nicept签到结果 ----\n{self.sign(cookie)}"
            msg_all += msg + "\n\n"
        return msg_all


if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("NICEPT", [])
    result = nicept(check_items=_check_items).main()
    send("nicept", result)
    # print(result)
