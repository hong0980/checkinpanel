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
        session = requests.session()
        res = ""
        url = 'http://pthome.net/attendance.php'
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/102.0.0.0 Safari/537.36",
        }
        r = session.get(url, headers=headers)
        if "欢迎回来" in r.text:
            pattern = r'使用</a>]: (.*?)&nbsp;.*?做种积分.*?</a>(.*?)\s*<font.*?分享率：</font>\s*(.*?)\s*<font.*?上传量：</font>\s*(.*?)\s*<font.*?下载量：</font>\s*(.*?)\s*<font.*?当前做种.*?>\s*(\d+)\s*<'
            result = re.findall(pattern, r.text, re.DOTALL)[0]
            msg = (f'<b>账户信息：</b>\n'
                   f'魔力值：{result[0]}\n'
                   f'做种积分：{result[1]}\n'
                   f'分享率：{result[2]}\n'
                   f'上传量：{result[3]}\n'
                   f'下载量：{result[4]}\n'
                   f'当前做种：{result[5]}\n'
            )
            if "签到成功" in r.text:
                g = re.findall(r'<p>(这是您.*?魔力值。)</p>', r.text)[0]
                res += f"<b><span style='color: green'>签到成功</span></b>\n{g}\n\n{msg}" 
            elif "抱歉" in r.text:
                g = re.findall(r'\((签到已得\d+)\)', r.text)[0]
                res += f"<b><span style='color: green'>您今天已经签到过了，请勿重复刷新。</span></b>\n{g}\n\n{msg}"
            else:
                res = "<b><span style='color: red'>签到失败</span></b>"
        else:
            res = "<b><span style='color: red'>cookie 失效</span></b>"
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
