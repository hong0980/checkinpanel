# -*- coding: utf-8 -*-
"""
cron: 55 59 15,23 * * *
new Env('NicePT 签到');
"""

import re, time
from utils import get_data
from notify_mtr import send
from requests_html import HTMLSession
from datetime import datetime, timedelta

class NicePT:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        msg, now, s, headers = '', datetime.now(), HTMLSession(), {'Cookie': cookie}
        sign_msg = '<b><span style="color: purple">你今天已经签到了，请勿重复签到</span></b>'
        if now.hour == 23 and 57 <= now.minute <= 59:
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            sleep_seconds = (midnight - now).total_seconds()
            print(f'等待{int(sleep_seconds)}秒后执行签到！')
            time.sleep(sleep_seconds)

        r = s.get('https://www.nicept.net/torrents.php', headers=headers)
        name = re.findall(r'<b>(.*?)</b>', r.text)
        name = name[0] if name else None
        if name is None:
            return (f"<b><span style='color: red'>签到失败</span></b>\n"
                    f"账号({i})无法登录！可能Cookie失效，请重新修改")

        if not '簽到已得' in r.text:
            r = s.get('https://www.nicept.net/attendance.php', headers=headers)
            now_time = datetime.now().time()
            details = re.findall(r'<p>(這是您的第.*?個魔力值。).*?(今日簽到排名：.*?)</span>', r.text)[0]
            msg = f'{details[0]}{details[1]}\n'
            sign_msg = f"<b><span style='color: green'>签到成功。</span></b> {now_time}"
            if "簽到成功" not in r.text:
                sign_msg = "<b><span style='color: red'>签到失败！</span></b>"

        pattern = (r'魔力值.*?:\s*(.*?)\s*<a.*?'
                   r'分享率：</font>\s*(.*?)\s*<font.*?'
                   r'上傳量：</font>\s*(.*?)\s*<font.*?'
                   r'下載量：</font>\s*(.*?)\s*<font.*?'
                   r'當前做種.*?>(\d+)\s*<img')
        result = re.findall(pattern, r.text, re.DOTALL)[0]
        msg += (f'\n<b>账户信息：</b>\n'
                f'魔力值：{result[0]}\n'
                f'分享率：{result[1]}\n'
                f'上传量：{result[2]}\n'
                f'下载量：{result[3]}\n'
                f'当前做种：{result[4]}\n')

        return (f"---- {name} NicePT 签到结果 ----\n"
                f"{sign_msg}\n{msg}")

    def main(self):
        msg_all = ''
        for i, check_item in enumerate(self.check_items, start=1):
            msg_all += f'{self.sign(check_item.get("cookie"), i)}\n\n'
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("NICEPT", [])
    result = NicePT(check_items=_check_items).main()
    send("NicePT 签到", result)
    # print(result)
