# -*- coding: utf-8 -*-
"""
cron: 0 0 * * *
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
        session = requests.session()
        url = 'https://www.nicept.net/attendance.php'
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/102.0.0.0 Safari/537.36",
        }
        r = session.get(url, headers=headers)

        if "登錄" in r.text:
            return 'cookie 失效'

        if "簽到成功" in r.text:
            account_pattern = r'魔力值.*?\]:\s*(.*?)\s*<a.*?分享率：</font>\s*([\d.]+)\s*.*?上傳量：</font>\s*([\d.]+\s*[A-Z]+).*?下載量：</font>\s*([\d.]+\s*[A-Z]+).*?"當前做種".*?>\s*(\d+)\s*<img'
            account_info = re.findall(account_pattern, r.text, re.DOTALL)
            
            if account_info:
                result = account_info[0]
                msg = (f'<b>账户信息：</b>\n'
                       f'魔力值：{result[0]}\n'
                       f'分享率：{result[1]}\n'
                       f'上传量：{result[2]}\n'
                       f'下载量：{result[3]}\n'
                       f'当前做种：{result[4]}\n'
                      )
            else:
                msg = '<b>账户信息获取失败。</b>\n'

            details_pattern = r'<p>(這是您的第 <b>\d+</b> 次簽到，已連續簽到 <b>\d+</b> 天，本次簽到獲得 <b>\d+</b> 個魔力值。).*?(今日簽到排名：<b>\d+</b> / <b>\d+</b>)</span>'
            details = re.findall(details_pattern, r.text, re.DOTALL)
            p = f'{details[0][0]}{details[0][1]}' if details else '签到信息获取失败'

            res += f"<b><span style='color: green'>签到成功。</span></b>\n{p}\n\n{msg}"
        else:
            res = "<b><span style='color: red'>签到失败</span></b>"

        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            msg = f"---- 账号({i}) nicept 签到结果 ----\n{self.sign(cookie)}"
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("NICEPT", [])
    result = nicept(check_items=_check_items).main()
    send("nicept", result)
    # print(result)
