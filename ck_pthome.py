# -*- coding: utf-8 -*-
"""
cron: 1 0 * * *
new Env('pthome 签到');
"""
import re
import requests
from notify_mtr import send
from utils import get_data

class pthome:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie):
        res = ""
        url = 'http://pthome.net/attendance.php'
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/102.0.0.0 Safari/537.36",
        }
        response = requests.post(url, headers=headers)
        if "PTHOME" in response.text:
            if "签到成功" in response.text:
                # res += "pthome 签到成功\n" + ''.join(re.findall(r'<p>(.*?)</p>', response.text))
                res += "pthome 签到成功\n" + re.findall(r'<p>(.*?)</p>', response.text)[0]
            elif "抱歉" in response.text:
                res += "您今天已经签到过了，请勿重复刷新。"
            else:
                res += "签到失败"
        else:
            res += 'cookie 失效'
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            msg = f"---- 账号({i})pthome 签到结果 ----\n{self.sign(cookie)}"
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("PTHOME", [])
    result = pthome(check_items=_check_items).main()
    send("pthome", result)
    # print(result)
