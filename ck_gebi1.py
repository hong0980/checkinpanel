# -*- coding: utf-8 -*-
"""
cron: 55 59 11,23 * * *
new Env('隔壁网 签到');
"""

import re
import time
from utils import get_data
from notify_mtr import send
from requests_html import HTMLSession
from datetime import datetime, timedelta

class gebi1:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        res = ''
        url = 'https://www.gebi1.com/plugin.php?id=k_misign:sign'
        credit = 'https://www.gebi1.com/home.php?mod=spacecp&ac=credit'
        def countdown():
            now = datetime.now()
            if now.hour == 23 and 57 <= now.minute <= 59:
                midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1, seconds=2)
                sleep_seconds = (midnight - now).total_seconds()
                print(f'等待{int(sleep_seconds)}秒后执行签到！')
                time.sleep(sleep_seconds)

        try:
            countdown()
            with HTMLSession() as s:
                r = s.get(url, headers={"Cookie": cookie}, timeout=10)
                if not '我的空间' in r.text:
                    return f'账号({i})无法登录！可能Cookie失效，请重新修改'

                msg = f"---- {r.html.find('a.author')[0].text} 隔壁网 签到结果 ----\n"
                res = f"{msg}<b><span style='color: green'>今日已签到</span></b>\n"
                JD_sign = r.html.find('a#JD_sign', first=True)

                if JD_sign:
                    sign_link = 'https://www.gebi1.com/' + JD_sign.attrs['href']
                    s.get(sign_link, headers={"Cookie": cookie})
                    now_time = datetime.now().time()
                    time.sleep(2)
                    r = s.get(url, headers={"Cookie": cookie})
                    if not r.html.find('a#JD_sign', first=True):
                        res = f"{msg}<b><span style='color: green'>签到成功</span></b> {now_time}\n"

                res += (
                    f'签到排名：{r.html.find("#qiandaobtnnum", first=True).attrs["value"]}\n'
                    f'连续签到：{r.html.find("#lxdays", first=True).attrs["value"]} 天\n'
                    f'签到等级：LV.{r.html.find("#lxlevel", first=True).attrs["value"]}\n'
                    f'积分奖励：{r.html.find("#lxreward", first=True).attrs["value"]} 条丝瓜\n'
                    f'累计签到：{r.html.find("#lxtdays", first=True).attrs["value"]} 天\n\n'
                )

                response = s.get(credit, headers={"Cookie": cookie})
                pattern = r'<em>\s*(丝瓜|经验值|积分|贡献):\s*</em>(\d+)'
                matches = re.findall(pattern, response.text)
                res += '<b>我的积分:</b>\n' + ''.join([f'{match[0]}: {match[1]}\n' for match in matches])

        except AttributeError as e:
            res += f"签到失败: 属性错误 - {str(e)}"
        except Exception as e:
            res += f"签到失败: {str(e)}"
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = str(check_item.get("cookie"))
            msg = self.sign(cookie, i)
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("GEBI1", [])
    result = gebi1(check_items=_check_items).main()
    send("隔壁网", result)
    # print(result)
