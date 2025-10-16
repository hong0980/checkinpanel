# -*- coding: utf-8 -*-
"""
cron: 10 1 0,15 * * *
new Env('PTHOME 签到');
"""
import re, requests
from notify_mtr import send
from utils import get_data, store

class PTHOME:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        signKey = f"pthome_sign_{i}"
        if store.has_signed(signKey):
            return (f"账号 {i}: ✅ 今日已签到")

        session = requests.session()
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/102.0.0.0 Safari/537.36",
        }
        r = session.get('http://pthome.net/attendance.php', headers=headers)
        if r.status_code == 200:
            name = re.findall(r'<b>(.*?)</b>', r.text)
            name = name[0] if name else None
            if name is None:
                return (f"<b><span style='color: red'>签到失败</span></b>\n"
                        f"账号({i})无法登录！可能Cookie失效，请重新修改")

            pattern = (r'使用</a>]: (.*?)&nbsp;.*?'
                       r'做种积分.*?</a>(.*?)\s*<font.*?'
                       r'分享率：</font>\s*(.*?)\s*<font.*?'
                       r'上传量：</font>\s*(.*?)\s*<font.*?'
                       r'下载量：</font>\s*(.*?)\s*<font.*?'
                       r'当前做种.*?>\s*(\d+)\s*<')
            result = re.findall(pattern, r.text, re.DOTALL)[0]
            msg = (f'<b>账户信息：</b>\n'
                   f'魔力值：{result[0]}\n做种积分：{result[1]}\n'
                   f'分享率：{result[2]}\n上传量：{result[3]}\n'
                   f'下载量：{result[4]}\n当前做种：{result[5]}')

            res = f"---- {name} PTHOME 签到结果 ----\n"
            if "签到成功" in r.text:
                store.mark_signed(signKey)
                g = re.findall(r'<p>(这是您.*?魔力值。)</p>', r.text)[0]
                return f"{res}<b><span style='color: green'>签到成功</span></b>\n{g}\n\n{msg}"
            elif "抱歉" in r.text:
                g = re.findall(r'\((签到已得\d+)\)', r.text)[0]
                return (f"{res}<b><span style='color: green'>您今天已经签到过了，请勿重复刷新。</span></b>"
                        f"\n今天{g}魔力值\n\n{msg}")
            else:
                return f"{res}<b><span style='color: red'>签到失败</span></b>"
        else:
            return f"请求失败，状态码：{r.status_code}"

    def main(self):
        msg_all = ''
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            msg_all += f'{self.sign(cookie, i)}\n\n'
        return msg_all

if __name__ == "__main__":
    result = PTHOME(check_items=get_data().get("PTHOME", [])).main()
    if '获得' in result or '失败' in result:
        send("PTHOME 签到", result)
    else:
        print(result)
    # print(result)
