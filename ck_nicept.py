# -*- coding: utf-8 -*-
"""
cron: 55 59 15,23 * * *
new Env('NicePT 签到');
"""

import re, time, requests
from utils import get_data
from notify_mtr import send
from datetime import datetime, timedelta

class NicePT:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        now, s, headers, msg = datetime.now(), requests.session(), {'Cookie': cookie}, \
            f'<b><span style="color: purple">你今天已经签到了，请勿重复签到</span></b>\n'
        if now.hour == 23 and 57 <= now.minute <= 59:
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            sleep_seconds = (midnight - now).total_seconds()
            print(f'等待{int(sleep_seconds)}秒后执行签到！')
            time.sleep(sleep_seconds)

        r = s.get(f'https://www.nicept.net/torrents.php', headers=headers)
        if r.status_code == 200:
            name = re.findall(r"class='NexusMaster_Name'><b>(.*?)</b>", r.text)
            name = name[0] if name else None
            if name is None:
                return (f"<b><span style='color: red'>签到失败</span></b>\n"
                        f"账号({i})无法登录！可能Cookie失效，请重新修改")

            if '[簽到得魔力]' in r.text:
                r = s.get(f'https://www.nicept.net/attendance.php', headers=headers)
                m = re.search(r'<p>(這是您的第.*?個魔力值。).*?(今日簽到排名：.*?)</span>', r.text)
                msg = (f"<b><span style='color: green'>签到成功。</span></b> "
                       f"{datetime.now().time()}\n{m.group(1)}{m.group(2)}\n"
                       if m and "獲得" in m.group(1) else f"<b><span style='color: red'>签到失败！</span></b>\n")

            pattern = (r'魔力值.*?:\s*(.*?)\s*<a.*?'
                       r'分享率：</font>\s*(.*?)\s*<font.*?'
                       r'上傳量：</font>\s*(.*?)\s*<font.*?'
                       r'下載量：</font>\s*(.*?)\s*<font.*?'
                       r'當前做種.*?>(\d+)\s*<img')
            m = re.search(pattern, r.text, re.DOTALL)
            msg += (f'\n<b>账户信息：</b>\n'
                    f'魔力值：{m.group(1)}\n'
                    f'分享率：{m.group(2)}\n'
                    f'上传量：{m.group(3)}\n'
                    f'下载量：{m.group(4)}\n'
                    f'当前做种：{m.group(5)}')

            return f"---- {name} NicePT 签到结果 ----\n{msg}"
        else:
            return f"请求失败，状态码：{r.status_code}"

    def main(self):
        msg_all = ''
        for i, check_item in enumerate(self.check_items, start=1):
            msg_all += f'{self.sign(check_item.get("cookie"), i)}\n\n'
        return msg_all

if __name__ == "__main__":
    result = NicePT(check_items=get_data().get("NICEPT", [])).main()
    if '獲得' in result or '签到失败' in result or '请求失败' in result:
        send("NicePT 签到", result)
    else:
        print(result)
