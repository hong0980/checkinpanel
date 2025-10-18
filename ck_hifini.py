# -*- coding: utf-8 -*-
"""
cron: 45 58 23,11 * * *
new Env('HIFITI 签到');
"""

import re
from notify_mtr import send
from requests_html import HTMLSession
from utils import get_data, store, wait_midnight, setup_hooks

def hifiti_sign(cookies, i):
    signKey = f"hifiti_sign_{i}"
    if store.has_signed(signKey, tomorrow_if_late=True): return (f"账号 {i}: ✅ 今日已签到")

    url = "https://www.hifiti.com/"
    message = "<b><span style='color: red'>签到失败/span></b>"
    session = HTMLSession()
    # setup_hooks(session, truncate=0)
    headers = {
        'cookie': cookies,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/134.0.0.0 Safari/537.36',
    }
    try:
        g = session.get(url, headers=headers)
        name_element = g.html.find('a[href="my.htm"]', first=True)
        if name_element is None:
            return (f"{message}账号({i})无法登录！可能Cookie失效，请重新修改")

        wait_midnight()
        # sign = re.search(r"var s1 = '(.+?)'", g.text)
        # if '签到' in sign.group(1):
        postheaders = {
            **headers,
            'origin': url, 'referer': url,
            'x-requested-with': 'XMLHttpRequest',
        }
        p = session.post(f'{url}sg_sign.htm', headers=postheaders)
        now = store.now()
        print(p.text)
        if p.status_code == 200:
            store.mark_signed(signKey)
            message = p.json().get("message")
        g = session.get(url, headers=headers)

        lt = re.search(r"var s3 = '(.+?)'", g.text)
        if lt:
            message += f"\n当前{lt.group(1)}"

        f = session.get(f'{url}my-credits.htm', headers=headers)
        schedule = re.findall(r'<p>(用户组: .*?)</p>', f.text)[0]
        schedule += ' ' + f.html.find('div.progress', first=True).text
        matches = re.findall(r'(经验|金币|人民币).*?value="(\d+)"', f.text)
        res = ''.join([f'{match[0]}: {match[1]}\n' for match in matches])
        name = name_element.text.strip()
        return (f"--- {name} HIFITI 签到结果 ---\n{message}\n{now}\n"
                f"<b>账户信息</b>\n{schedule}\n{res}")

    except Exception as e:
        return f" 操作异常{str(e)}"

def hifiti_main(check_items):
    msg_all = ''
    for i, item in enumerate(check_items, start=1):
        msg_all += f'{hifiti_sign(item.get("cookie"), i)}\n\n'
    return msg_all

if __name__ == "__main__":
    result = hifiti_main(get_data().get("HIFINI", []))
    if re.search(r'成功|失败|登录|异常', result):
        send("HIFITI 签到", result)
    else:
        print(result)
    # print(result)
