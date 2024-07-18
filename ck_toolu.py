# -*- coding: utf-8 -*-
"""
cron: 3 0 * * *
new Env('在线工具 签到');
"""

import re
import requests
from utils import get_data
from notify_mtr import send

class ToolLu:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        headers = {
            "cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/102.0.0.0 Safari/537.36",
        }

        try:
            session = requests.Session()
            r = session.get('https://id.tool.lu/sign', headers=headers)
            if '登录' in r.text:
                return f'账号({i})无法登录！可能Cookie失效，请重新修改'

            a = re.findall(r'<div class="mb-6">(.*?)，(你已经连续签到 \d+ 天)，再接再厉！</div>', r.text)

            if not a:
                return "<b><span style='color: green'>在线工具 签到失败</span></b>"

            c = session.get('https://id.tool.lu/credits', headers=headers)
            d = re.findall(r'>(每日签到获得 \d+ 积分)</td>', c.text)
            t = re.findall(r'<div class="mb-6">(最近签到时间.*?)</div>', r.text)
            e = re.findall(r'>(.*?)<span class="badge bg-warning">(.*?)</span>', c.text)

            return (
                f"---- {a[0][0]} 在线工具 签到结果 ----\n"
                f"<b><span style='color: green'>签到成功</span></b>\n"
                f"{d[0]}\n{a[0][1]}\n{e[0][0]}{e[0][1]}\n{t[0]}"
            )

        except requests.RequestException as e:
            return f"请求出错: {e}"
        except Exception as e:
            return f"<b><span style='color: red'>未知异常：</span></b>\n{e}"

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            msg = self.sign(cookie, i)
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("TOOLU", [])
    result = ToolLu(check_items=_check_items).main()
    send("在线工具", result)
    # print(result)
