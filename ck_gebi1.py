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
        res = []
        session = requests.session()
        url = 'https://www.gebi1.com/plugin.php?id=k_misign:sign'
        credit = 'https://www.gebi1.com/home.php?mod=spacecp&ac=credit'
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/102.0.0.0 Safari/537.36",
        }

        def parse_sign_info(soup):
            lxdays = soup.select_one('#lxdays')['value']
            lxtdays = soup.select_one('#lxtdays')['value']
            lxlevel = soup.select_one('#lxlevel')['value']
            lxreward = soup.select_one('#lxreward')['value']
            qiandaobtnnum = soup.select_one('#qiandaobtnnum')['value']
            res = (
                f'签到排名：{qiandaobtnnum}\n'
                f'连续签到：{lxdays} 天\n'
                f'签到等级：LV.{lxlevel}\n'
                f'积分奖励：{lxreward} 条丝瓜\n'
                f'累计签到：{lxtdays} 天'
            )

            response = session.get(credit, headers=headers, timeout=10)
            pattern = r'<em>\s*(丝瓜|经验值|积分|贡献):\s*</em>(\d+)'
            matches = re.findall(pattern, response.text)
            res += '\n\n<b>我的积分:</b>\n' + ''.join([f'{match[0]}: {match[1]}\n' for match in matches])

            return res

        try:
            r = session.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            if '注册' in r.text:
                return 'cookie失效'

            sign_href = soup.find('a', id='JD_sign')
            if sign_href:
                sign_link = 'https://www.gebi1.com/' + sign_href.get('href')
                session.get(sign_link, headers=headers, timeout=10)
                sleep(2)
                r = session.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(r.text, "html.parser")
                res.append(f"<b><span style='color: green'>签到成功</span></b>\n{parse_sign_info(soup)}")
            else:
                res.append(f"<b><span style='color: green'>今日已签到</span></b>\n{parse_sign_info(soup)}")

        except requests.Timeout:
            res.append("签到失败: 请求超时")
        except requests.RequestException as e:
            res.append(f"签到失败: 网络请求异常 - {str(e)}")
        except AttributeError as e:
            res.append(f"签到失败: 属性错误 - {str(e)}")
        except Exception as e:
            res.append(f"签到失败: {str(e)}")

        return '\n'.join(res)

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
