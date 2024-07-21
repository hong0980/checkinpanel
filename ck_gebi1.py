# -*- coding: utf-8 -*-
"""
cron: 55 59 11,23 * * *
new Env('隔壁网 签到');
"""

import re
import time
import requests
from utils import get_data
from notify_mtr import send
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

class gebi1:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        res = ''
        session = requests.session()
        url = 'https://www.gebi1.com/plugin.php?id=k_misign:sign'
        credit = 'https://www.gebi1.com/home.php?mod=spacecp&ac=credit'
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/102.0.0.0 Safari/537.36",
        }
        def countdown():
            now = datetime.now()
            if now.hour == 23 and 57 <= now.minute <= 59:
                midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                sleep_seconds = (midnight - now).total_seconds()
                print(f'等待{int(sleep_seconds)}秒后执行签到！')
                time.sleep(sleep_seconds)

        try:
            countdown()
            r = session.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            if not '我的空间' in r.text:
                return f'账号({i})无法登录！可能Cookie失效，请重新修改'

            name = soup.find_all('a', class_='author')
            msg = f"---- {name[0].text} 隔壁网 签到结果 ----\n"
            res = f"{msg}<b><span style='color: green'>今日已签到</span></b>\n"
            JD_sign = soup.select_one('#JD_sign')
            if JD_sign:
                sign_link = 'https://www.gebi1.com/' + JD_sign['href']
                session.get(sign_link, headers=headers, timeout=10)
                now_time = datetime.now().time()
                time.sleep(2)
                r = session.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(r.text, "html.parser")
                res = f"{msg}<b><span style='color: green'>签到成功</span></b> {now_time}\n"

            res += (
                f'签到排名：{soup.select_one("#qiandaobtnnum")["value"]}\n'
                f'连续签到：{soup.select_one("#lxdays")["value"]} 天\n'
                f'签到等级：LV.{soup.select_one("#lxlevel")["value"]}\n'
                f'积分奖励：{soup.select_one("#lxreward")["value"]} 条丝瓜\n'
                f'累计签到：{soup.select_one("#lxtdays")["value"]} 天\n\n'
            )

            response = session.get(credit, headers=headers, timeout=10)
            pattern = r'<em>\s*(丝瓜|经验值|积分|贡献):\s*</em>(\d+)'
            matches = re.findall(pattern, response.text)
            res += '<b>我的积分:</b>\n' + ''.join([f'{match[0]}: {match[1]}\n' for match in matches])

        except requests.Timeout:
            res += "签到失败: 请求超时"
        except requests.RequestException as e:
            res += f"签到失败: 网络请求异常 - {str(e)}"
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
