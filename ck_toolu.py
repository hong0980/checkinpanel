# -*- coding: utf-8 -*-
"""
cron: 30 1 0 * * *
new Env('在线工具 签到');
"""

from utils import get_data
from notify_mtr import send
import re, requests, datetime

class ToolLu:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        try:
            s = requests.Session()
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            r = s.get('https://id.tool.lu/sign', headers={
                   "cookie": cookie,
                   "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/102.0.0.0 Safari/537.36"})
            a = re.findall(r'<div class="mb-6">(.*?)，(你已经连续签到 \d+ 天)，再接再厉！</div>', r.text)
            name, consecutive_sign_in = (a[0][0], a[0][1]) if a else (None, '')
            if name is None:
                return (f"<b><span style='color: red'>签到失败</span></b>\n"
                        f"账号({i})无法登录！可能Cookie失效，请重新修改")

            c = s.get('https://id.tool.lu/credits')
            match = re.search(rf'{current_date}.*?积分</td>', c.text, re.DOTALL)
            consecutive = re.findall(rf'{current_date}.*?(连续.*?积分)</td>', match.group(0), re.DOTALL)
            consecutive = consecutive + '\n' if consecutive else ''
            daily_points = re.findall(rf'{current_date}.*?(每日.*?积分)</td>', c.text, re.DOTALL)[0]
            points = re.findall(r'>(.*?)<span class="badge bg-warning">(.*?)</span>', c.text)[0]
            last_time = re.findall(rf'<div class="mb-6">(最近签到时间：{current_date}.*?)</div>', r.text)
            color, status, last_time = ('green', '成功', last_time[0]) if last_time else ('red', '失败', '')

            return (f"---- {name} 在线工具 签到结果 ----\n"
                    f"<b><span style='color: {color}'>签到{status}</span></b>\n\n"
                    f"<b>账户信息</b>\n{consecutive_sign_in}\n{daily_points}\n"
                    f"{consecutive}{points[0]}{points[1]}\n{last_time}")

        except Exception:
            import traceback
            return f"<b><span style='color: red'>未知异常：</span></b>\n{traceback.format_exc()}"

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
