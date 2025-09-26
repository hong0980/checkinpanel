# -*- coding: utf-8 -*-
"""
cron: 45 58 15,23 * * *
new Env('HIFITI 签到');
"""

import re, time
from notify_mtr import send
from datetime import datetime, timedelta
from requests_html import HTMLSession
from utils import get_data, today, read, write

class HIFITI:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookies, i):
        signKey = f"hifiti_sign_{i}"
        if read(signKey) == today():
            return (f"账号 {i}: ✅ 今日已签到")
        day, now, s = '', datetime.now(), HTMLSession()
        url = "https://www.hifiti.com/"
        message = "<b><span style='color: red'>签到失败/span></b>"
        headers = {
            'cookie': cookies,
            "pragma": "no-cache",
            "cache-control": "no-cache",
            'authority': 'www.hifini.com',
            'referer': 'https://www.hifiti.com/',
            "accept": "application/json, text/javascript, */*; q=0.01",
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        }

        r = s.get(url, headers=headers)
        name_element = r.html.find('a[href="my.htm"]', first=True)
        name = name_element.text.strip()
        if name is None:
            return (f"<b><span style='color: red'>签到失败</span></b>\n"
                    f"账号({i})无法登录！可能Cookie失效，请重新修改")

        if now.hour == 23 and 57 <= now.minute <= 59:
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            sleep_seconds = (midnight - now).total_seconds()
            print(f'等待{int(sleep_seconds)}秒后执行签到！')
            time.sleep(sleep_seconds)

        headers.update({
            'referer': 'https://www.hifiti.com/',
            'origin': 'https://www.hifiti.com',
            'x-requested-with': 'XMLHttpRequest',
            })
        p = s.post('https://www.hifiti.com/sg_sign.htm', headers=headers)
        headers.pop('X-Requested-With', None)
        if p.status_code == 200:
            write(signKey, today())
            message = f'{p.json().get("message")}'
            r = s.get(url, headers=headers)
            day = f'当前{re.findall(r"连续签到.*?天", r.text)[0]}\n'

        f = s.get('https://www.hifiti.com/my-credits.htm', headers=headers)
        matches = re.findall(r'(经验|金币|人民币).*?value="(\d+)"', f.text)
        res = ''.join([f'{match[0]}: {match[1]}\n' for match in matches])
        group = re.findall(r'<p>(用户组: .*?)</p>', f.text)[0]
        schedule = f.html.find('div.progress', first=True).text
        return (f"--- {name} HIFITI 签到结果 ---\n{message}\n"
                f"{day}\n<b>账户信息</b>\n{group}  {schedule}\n{res}")

    def main(self):
        msg_all = ''
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            msg_all += f'{self.sign(cookie, i)}\n\n'
        return msg_all

if __name__ == "__main__":
    result = HIFITI(check_items=get_data().get("HIFINI", [])).main()
    if any(x in result for x in ['成功', '失败']):
        send("HIFITI 签到", result)
    else:
        print(result)
