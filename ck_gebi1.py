# -*- coding: utf-8 -*-
"""
cron: 0 0 * * *
new Env('隔壁网 签到');
"""
import re
import requests
from time import sleep
from utils import get_data
from notify_mtr import send
from bs4 import BeautifulSoup

class gebi1:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie):
        res = ""
        session = requests.session()
        url = 'https://www.gebi1.com/plugin.php?id=k_misign:sign'
        qd_url = 'https://www.gebi1.com/plugin.php?id=k_misign:sign&operation=qiandao&formhash=188fd2da&format=empty'
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/102.0.0.0 Safari/537.36",
        }

        def parse_sign_info(soup):
            lxdays = soup.select_one('#lxdays')['value']
            lxlevel = soup.select_one('#lxlevel')['value']
            lxreward = soup.select_one('#lxreward')['value']
            lxtdays = soup.select_one('#lxtdays')['value']
            qiandaobtnnum = soup.select_one('#qiandaobtnnum')['value']
            return lxdays, lxlevel, lxreward, lxtdays, qiandaobtnnum

        try:
            response = session.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            if '注册' in response.text:
                res += 'cookie失效'
            else:
                if '您今天还没有签到' in response.text:
                    session.get(qd_url, headers=headers, timeout=10)
                    sleep(2)
                    response = session.get(url, headers=headers, timeout=10)
                    soup = BeautifulSoup(response.text, "html.parser")
                    lxdays, lxlevel, lxreward, lxtdays, qiandaobtnnum = parse_sign_info(soup)
                    res += f"签到成功\n签到排名：{qiandaobtnnum}\n连续签到：{lxdays}\n签到等级：{lxlevel}\n积分奖励：{lxreward}\n总天数：{lxtdays}"
                else:
                    lxdays, lxlevel, lxreward, lxtdays, qiandaobtnnum = parse_sign_info(soup)
                    res += f"今日已签到\n签到排名：{qiandaobtnnum}\n连续签到：{lxdays}\n签到等级：{lxlevel}\n积分奖励：{lxreward}\n总天数：{lxtdays}"
        except requests.RequestException as e:
            res += f"网络请求异常: {str(e)}"
        except Exception as e:
            res += f"发生异常: {str(e)}"
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = str(check_item.get("cookie"))
            msg = f"---- 账号({i})隔壁网签到结果 ----\n{self.sign(cookie)}"
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("GEBI1", [])
    result = gebi1(check_items=_check_items).main()
    send("隔壁网", result)
    # print(result)
