# -*- coding: utf-8 -*-
"""
cron: 45 58 15,23 * * *
new Env('HiFiNi 签到');
"""

import re, time
from utils import get_data
from notify_mtr import send
from datetime import datetime, timedelta
from requests_html import HTMLSession

class HiFiNi:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookies, i):
        day, now, s = '', datetime.now(), HTMLSession()
        url = "https://www.hifini.com/sg_sign.htm"
        message = "<b><span style='color: red'>签到失败/span></b>"
        headers = {
            'cookie': cookies,
            "pragma": "no-cache",
            "cache-control": "no-cache",
            'authority': 'www.hifini.com',
            'referer': 'https://www.hifini.com/',
            "accept": "application/json, text/javascript, */*; q=0.01",
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        }

        r = s.get(url, headers=headers)
        name = r.html.find('li.username', first=True)
        if name is None:
            return (f"<b><span style='color: red'>签到失败</span></b>\n"
                    f"账号({i})无法登录！可能Cookie失效，请重新修改")

        if now.hour == 23 and 57 <= now.minute <= 59:
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            sleep_seconds = (midnight - now).total_seconds()
            print(f'等待{int(sleep_seconds)}秒后执行签到！')
            time.sleep(sleep_seconds)

        sign = re.findall(r'sign = "(\w+)"', r.text)
        headers.update({'X-Requested-With': 'XMLHttpRequest'})
        p = s.post(url, data={'sign': sign[0]}, headers=headers)
        headers.pop('X-Requested-With', None)

        if p.status_code == 200:
            message = f'{p.json().get("message")}'
            r = s.get(url, headers=headers)
            day = f'当前{re.findall(r"连续签到 .*? 天", r.text)[0]}\n'

        f = s.get('https://www.hifini.com/my-credits.htm', headers=headers)
        matches = re.findall(r'(经验|金币|人民币).*?value="(\d+)"', f.text)
        res = ''.join([f'{match[0]}: {match[1]}\n' for match in matches])
        group = re.findall(r'<p>(用户组: .*?)</p>', f.text)[0]
        schedule = f.html.find('div.progress', first=True).text
        return (f"--- {name.text} HiFiNi 签到结果 ---\n{message}\n"
                f"{day}\n<b>账户信息</b>\n{group}  {schedule}\n{res}")

    def main(self):
        msg_all = ''
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            msg_all += f'{self.sign(cookie, i)}\n\n'
        return msg_all

if __name__ == "__main__":
    result = HiFiNi(check_items=get_data().get("HIFINI", [])).main()
    if '已经签过' in result:
        print(result)
    else:
        send("HiFiNi 签到", result)
