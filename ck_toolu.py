# -*- coding: utf-8 -*-
"""
cron: 4 0 * * *
new Env('在线工具 签到');
"""

import re, requests
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
            a = re.findall(r'<div class="mb-6">(.*?)，(你已经连续签到 \d+ 天)，再接再厉！</div>', r.text)
            name = a[0][0] if a else None
            if name is None:
                return (f"<b><span style='color: red'>签到失败</span></b>\n"
                        f"账号({i})无法登录！可能Cookie失效，请重新修改")

            c = session.get('https://id.tool.lu/credits', headers=headers)
            d = re.findall(r'>(每日签到获得 \d+ 积分)</td>', c.text)[0]
            t = re.findall(r'<div class="mb-6">(最近签到时间.*?)</div>', r.text)[0]
            e = re.findall(r'>(.*?)<span class="badge bg-warning">(.*?)</span>', c.text)[0]

            return (
                f"---- {name} 在线工具 签到结果 ----\n"
                f"<b><span style='color: green'>签到成功</span></b>\n\n"
                f"<b>账户信息</b>\n"
                f"{d}\n{a[0][1]}\n{e[0]}{e[1]}\n{t}"
            )

        except requests.RequestException as e:
            return f"请求出错: {e}"
        except Exception as e:
            return f"<b><span style='color: red'>未知异常：</span></b>\n{e}"

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            msg_all += f'{self.sign(cookie, i)}\n\n'
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("TOOLU", [])
    result = ToolLu(check_items=_check_items).main()
    send("在线工具 签到", result)
    # print(result)
