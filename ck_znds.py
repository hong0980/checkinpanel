# -*- coding: utf-8 -*-
"""
cron: 2 0 * * *
new Env('智能电视网 签到');
"""
import re
from time import sleep
from utils import get_data
from notify_mtr import send
from requests_html import HTML, HTMLSession

class znds:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        try:
            s = HTMLSession()
            url = 'https://www.znds.com/'
            s.headers.update({'referer': url, 'authority': 'www.znds.com'})
            s.cookies.set('Cookie', cookie)
            r = s.get(url)
            name = r.html.search('title="访问我的空间">{}</a>')
            name = name[0] if name else None
            if name is None:
                return f'账号({i})无法登录！可能Cookie失效，请重新修改'

            formhash = re.findall(r'action=logout&amp;formhash=(\w+)">退出', r.text)
            sign_url = (f'{url}plugin.php?id=ljdaka:daka&action=msg&formhash={formhash[0]}&'
                        'infloat=yes&handlekey=ljdaka&inajax=1&ajaxtarget=fwin_content_ljdaka')

            r = s.get(sign_url)
            msg = r.html.search('class="alert_info"><p>{}</p></div>')[0]
            msg = re.sub(r'</p><p>', '\n', msg) if '</p><p>' in msg else msg
            sign_msg = "<b><span style='color: red'>签到失败</span></b>"
            if '获得' in msg:
                sign_msg = (f"<b><span style='color: green'>签到成功</span></b>\n"
                            f"<b><span style='color: orange'>{msg}</span></b>")
            elif '明日再来' in msg:
                sign_msg = f"<b><span style='color: orange'>{msg}</span></b>"

            f = s.get(f'{url}home.php?mod=spacecp&ac=credit')
            pattern = r'<em>\s*(金币|积分|威望|Z币):\s*</em>(\d+)'
            matches = re.findall(pattern, f.text)
            credit_info = ''.join([f'{match[0]}: {match[1]}\n' for match in matches])

            result = (f"-- {name} 智能电视网 签到结果 --"
                      f'\n{sign_msg}\n\n<b>账户信息</b>\n{credit_info}')

        except Exception as e:
            result = f"发生异常: {e}"
        finally:
            pass
        return result

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            msg_all += f'{self.sign(check_item.get("cookie"), i)}\n\n'
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("ZNDS", [])
    result = znds(check_items=_check_items).main()
    send("智能电视网  签到", result)
    # print(result)
