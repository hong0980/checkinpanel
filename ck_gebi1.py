# -*- coding: utf-8 -*-
"""
cron: 50 58 11,23 * * *
new Env('隔壁网 签到');
"""

import re, time
from notify_mtr import send
from requests_html import HTMLSession
from datetime import datetime, timedelta
from utils import get_data, today, read, write

class gebi1:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        signKey = f"gebi1_sign_{i}"
        if read(signKey) == today():
            return (f"账号 {i}: ✅ 今日已签到")
        url = 'https://www.gebi1.com/plugin.php?id=k_misign:sign'
        def countdown():
            now = datetime.now()
            if now.hour == 23 and 57 <= now.minute <= 59:
                midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                sleep_seconds = (midnight - now).total_seconds()
                print(f'等待{int(sleep_seconds)}秒后执行签到！')
                time.sleep(sleep_seconds)

        try:
            countdown()
            with HTMLSession() as s:
                s.cookies.set('Cookie', cookie)
                r = s.get(url)
                name = r.html.search('title="访问我的空间" class="kmname">{}</a>')
                name = name[0] if name else None
                if name is None:
                    return (f"<b><span style='color: red'>签到失败</span></b>\n"
                            f"账号({i})无法登录！可能Cookie失效，请重新修改")

                formhash = re.findall(r'action=logout&amp;formhash=(\w+)"', r.text)
                p = s.get(url, params = {
                    "operation": "qiandao", "format": "empty", "formhash": formhash[0]
                })
                msg = p.html.search('CDATA[{}]]')
                sign_msg = (f"<b><span style='color: green'>"
                            f"{msg[0] if msg else '签到成功'}</span></b> {datetime.now().time()}\n")
                if '成功' in sign_msg:
                    r = s.get(url)
                    write(signKey, today())

                credit_info = (f'签到排名：{r.html.find("#qiandaobtnnum")[0].attrs["value"]}\n'
                               f'连续签到：{r.html.find("#lxdays")[0].attrs["value"]} 天\n'
                               f'签到等级：LV.{r.html.find("#lxlevel")[0].attrs["value"]}\n'
                               f'积分奖励：{r.html.find("#lxreward")[0].attrs["value"]} 条丝瓜\n'
                               f'累计签到：{r.html.find("#lxtdays")[0].attrs["value"]} 天\n\n')

                response = s.get('https://www.gebi1.com/home.php?mod=spacecp&ac=credit')
                pattern = r'<em>\s*(丝瓜|经验值|积分|贡献):\s*</em>(\d+)'
                matches = re.findall(pattern, response.text)
                credit_info += '<b>账户信息</b>\n' + ''.join([f'{match[0]}: {match[1]}\n' for match in matches])
                result = (f"-- {name} 隔壁网 签到结果 --"
                          f'\n{sign_msg}{credit_info}')

        except AttributeError as e:
            result = f"签到失败: 属性错误 - {str(e)}"
        except Exception as e:
            result = f"签到失败: {str(e)}"
        finally:
            pass
        return result

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = str(check_item.get("cookie"))
            msg_all += f'{self.sign(cookie, i)}\n\n'
        return msg_all

if __name__ == "__main__":
    _check_items = get_data().get("GEBI1", [])
    result = gebi1(check_items=_check_items).main()
    if any(x in result for x in ['成功', '失败']):
        send("隔壁网 签到", result)
    else:
        print(result)
