# -*- coding: utf-8 -*-
"""
cron: 50 7 * * *
new Env('什么值得买APP');
"""

import json
import time
import hashlib
import requests
from utils import get_data
from notify_mtr import send


class Smzdm:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie):
        try:
            ts = int(round(time.time() * 1000))
            url = 'https://user-api.smzdm.com/robot/token'
            headers = {
                'Cookie': cookie,
                'Host': 'user-api.smzdm.com',
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'smzdm_android_V10.4.1 rv:841 (22021211RC;Android12;zh)smzdmapp',
            }
            data = {
                "f": "android",
                "v": "10.4.1",
                "weixin": 1,
                "time": ts,
                "sign": hashlib.md5(bytes(f'f=android&time={ts}&v=10.4.1&weixin=1&key=apr1$AwP!wRRT$gJ/q.X24poeBInlUJC', encoding='utf-8')).hexdigest().upper()
            }
            res = requests.post(url=url, headers=headers, data=data).json()
            token = res['data']['token']

            Timestamp = int(round(time.time() * 1000))
            data = {
                "f": "android",
                "v": "10.4.1",
                "weixin": 1,
                "token": token,
                "time": Timestamp,
                "sk": "ierkM0OZZbsuBKLoAgQ6OJneLMXBQXmzX+LXkNTuKch8Ui2jGlahuFyWIzBiDq/L",
                "sign": hashlib.md5(bytes(f'f=android&sk=ierkM0OZZbsuBKLoAgQ6OJneLMXBQXmzX+LXkNTuKch8Ui2jGlahuFyWIzBiDq/L&time={Timestamp}&token={token}&v=10.4.1&weixin=1&key=apr1$AwP!wRRT$gJ/q.X24poeBInlUJC', encoding='utf-8')).hexdigest().upper()
            }
            headers = {
                'Cookie': cookie,
                'Host': 'user-api.smzdm.com',
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'smzdm_android_V10.4.1 rv:841 (22021211RC;Android12;zh)smzdmapp',
            }
            url = 'https://user-api.smzdm.com/checkin/all_reward'
            res = requests.post(url=url, headers=headers, data=data).json()
            if '签到成功' in res:
                msg = (
                    f"<b><span style='color: green'>{res['data']['normal_reward']['title']}</span></b>\n"
                    f"{res['data']['normal_reward']['sub_title']}\n"
                    f"{res['data']['normal_reward']['gift']['title']}: "
                    f"{res['data']['normal_reward']['gift']['content_str']}\n"
                    f"{res['data']['normal_reward']['reward_add']['title']}: "
                    f"{res['data']['normal_reward']['reward_add']['content']}"
                )
            else:
                url = 'https://user-api.smzdm.com/checkin'
                res = requests.post(url=url, headers=headers, data=data).json()
                msg = (
                    f"<b><span style='color: green'>今天已经签到过了</span></b>\n{res['error_msg']}{res['data']['daily_num']}天\n"
                    f"金币{res['data']['cgold']}"
                )
        except Exception as e:
            msg = f"签到状态: 签到失败\n错误信息: {e}，请重新获取 cookie"
        return msg

    def main(self):
        msg_all = ""
        for check_item in self.check_items:
            msg = self.sign(check_item.get("cookie"))
            msg_all += msg + "\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("SMZDM", [])
    result = Smzdm(check_items=_check_items).main()
    send("什么值得买APP", result)
    # print(result)
