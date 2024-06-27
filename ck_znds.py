# -*- coding: utf-8 -*-
"""
cron: 3 0 * * *
new Env('智能电视网 签到');
"""
import re
import requests
from notify_mtr import send
from utils import get_data

class znds:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie):
        res = ""
        url = 'https://www.znds.com/plugin.php?id=ljdaka:daka&action=msg&formhash=a5bbc6d5&infloat=yes&handlekey=ljdaka&inajax=1&ajaxtarget=fwin_content_ljdaka'
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/102.0.0.0 Safari/537.36",
        }
        response = requests.post(url, headers=headers)

        if "CDATA" in response.text:
            matches = re.findall(r'<p>(.*?)</p>', response.text)[0]
            if "预计明日" in response.text:
                res += "签到成功\n" + matches
            elif "您已打卡" in response.text:
                res += matches
            else:
                res += "签到失败"
        else:
            res += 'cookie 失效'
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            msg = f"---- 账号({i}) 智能电视网 签到结果 ----\n{self.sign(cookie)}"
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("ZNDS", [])
    result = znds(check_items=_check_items).main()
    send("智能电视网", result)
    # print(result)
