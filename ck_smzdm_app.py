# -*- coding: utf-8 -*-
"""
cron: 50 7 * * *
new Env('什么值得买APP');
"""

import requests
import json
import time
import hashlib
from notify_mtr import send
from utils import get_data

class Smzdm:
    def __init__(self, check_items):
        self.check_items = check_items
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'smzdm_android_V11.0.17 rv:841 (22021211RC;Android12;zh)smzdmapp',
        }

    def get_token(self, cookie):
        ts = int(round(time.time() * 1000))
        url = 'https://user-api.smzdm.com/robot/token'
        data = {
            "time": ts,
            "weixin": 1,
            "f": "android",
            "v": "11.0.17",
            "sign": hashlib.md5(
                f'f=android&time={ts}&v=11.0.17&weixin=1&key=apr1$AwP!wRRT$gJ/q.X24poeBInlUJC'.encode('utf-8')
            ).hexdigest().upper()
        }
        response = requests.post(url=url, headers=self.headers, data=data, cookies={'Cookie': cookie})
        token = response.json()['data']['token']
        return token

    def sign(self, cookie):
        try:
            token = self.get_token(cookie)
            ts = int(round(time.time() * 1000))
            data = {
                "weixin": 1,
                "f": "android",
                "v": "11.0.17",
                "token": token,
                "time": ts,
                "sk": "ierkM0OZZbsuBKLoAgQ6OJneLMXBQXmzX+LXkNTuKch8Ui2jGlahuFyWIzBiDq/L",
                "sign": hashlib.md5(
                    f'f=android&sk=ierkM0OZZbsuBKLoAgQ6OJneLMXBQXmzX+LXkNTuKch8Ui2jGlahuFyWIzBiDq/L&time={ts}&token={token}&v=11.0.17&weixin=1&key=apr1$AwP!wRRT$gJ/q.X24poeBInlUJC'.encode('utf-8')
                ).hexdigest().upper()
            }
            url1 = 'https://user-api.smzdm.com/checkin'
            url2 = 'https://user-api.smzdm.com/checkin/all_reward'

            html1 = requests.post(url=url1, headers=self.headers, data=data, cookies={'Cookie': cookie})
            html2 = requests.post(url=url2, headers=self.headers, data=data, cookies={'Cookie': cookie})
            res1 = html1.json()
            res2 = html2.json()

            if res2['error_code'] == '0':
                msg = (
                    f"{res2['data']['normal_reward']['title']}\n"
                    f"{res2['data']['normal_reward']['sub_title']}\n"
                    f"{res2['data']['normal_reward']['reward_add']['title']}: "
                    f"{res2['data']['normal_reward']['reward_add']['content']}"
                )
            else:
                msg = (
                    f"重复签到\n{res1['error_msg']}{res1['data']['daily_num']}天\n"
                    f"金币{res1['data']['cgold']}"
                )
        except Exception as e:
            msg = f"签到状态: 签到失败\n错误信息: {e}，请重新获取 cookie"
        return msg

    def main(self):
        msg_all = ""
        for check_item in self.check_items:
            msg = self.sign(check_item.get("cookie"))
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("SMZDM", [])
    result = Smzdm(check_items=_check_items).main()
    send("什么值得买APP", result)
    # print(result)
