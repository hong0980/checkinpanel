# -*- coding: utf-8 -*-
"""
cron: 40 1 0 * * *
new Env('智能电视网 签到');
"""
import re
from time import sleep
from utils import get_data
from notify_mtr import send
from requests_html import HTMLSession

class znds:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        try:
            s = HTMLSession()
            url = 'https://www.znds.com/'
            s.cookies.set('Cookie', cookie)
            s.headers.update({'referer': url, 'authority': 'www.znds.com'})
            r = s.get(url)
            name = r.html.search('title="访问我的空间">{}</a>')
            name = name[0] if name else None
            if name is None:
                return f'账号({i})无法登录！可能Cookie失效，请重新修改'

            sign_msg = "<b><span style='color: red'>签到失败</span></b>"
            formhash = re.findall(r'action=logout&amp;formhash=(\w+)">退出', r.text)
            r = s.get(f'{url}plugin.php', params={
                'id': 'ljdaka:daka', 'handlekey': 'ljdaka',
                'inajax': '1', 'action': 'msg', 'infloat': 'yes',
                'formhash': formhash, 'ajaxtarget': 'fwin_content_ljdaka'
            })
            match = re.search(r'<div class="alert_info"><p>(.*?)</p></div>', r.text)
            if match:
                msg = re.sub(r'</p><p>', '\n', match.group(1))
                common_part = f"<b><span style='color: orange'>{msg}</span></b>"
                sign_msg = (f"<b><span style='color: green'>签到成功</span></b>\n{common_part}"
                            if '获得' in msg else common_part)

            f = s.get(f'{url}home.php?mod=spacecp&ac=credit')
            matches = re.findall(r'<em>\s*(金币|积分|威望|Z币):\s*</em>(\d+)', f.text)
            credit_info = ''.join([f'{match[0]}: {match[1]}\n' for match in matches])

            return (f"-- {name} 智能电视网 签到结果 --"
                    f'\n{sign_msg}\n\n<b>账户信息</b>\n{credit_info}')

        except Exception:
            import traceback
            return f"<b><span style='color: red'>未知异常：</span></b>\n{traceback.format_exc()}"

    def main(self):
        msg_all = ''
        for i, check_item in enumerate(self.check_items, start=1):
            msg_all += f'{self.sign(check_item.get("cookie"), i)}\n\n'
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("ZNDS", [])
    result = znds(check_items=_check_items).main()
    send("智能电视网  签到", result)
    # print(result)
