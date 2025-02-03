# -*- coding: utf-8 -*-
"""
cron: 53 11 * * *
new Env('吾爱破解');
"""
from time import sleep
import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from notify_mtr import send
from utils import get_data


class Pojie:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie):
        url, s, headers = 'https://www.52pojie.cn/forum.php', HTMLSession(), {'Cookie': cookie,}
        r = s.get(url, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        print(soup)

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            sign_msg = self.sign(cookie)
            msg = f"账号 {i} 签到状态: {sign_msg}"
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("POJIE", [])
    result = Pojie(check_items=_check_items).main()
    # send("吾爱破解", result)
    print(result)
