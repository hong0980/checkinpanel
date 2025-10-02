# -*- coding: utf-8 -*-
"""
cron: 45 58 23,11 * * *
new Env('HIFITI 签到');
"""

import re
from notify_mtr import send
from requests_html import HTMLSession
from utils import get_data, today, read, write, wait_midnight

def hifiti_sign(cookies, i):
    signKey = f"hifiti_sign_{i}"
    if read(signKey) == today(tomorrow_if_late=True):
        return (f"账号 {i}: ✅ 今日已签到")

    url = "https://www.hifiti.com/"
    message = "<b><span style='color: red'>签到失败/span></b>"
    session = HTMLSession()
    session.headers.update({
        'cookie': cookies, 'accept-language': 'zh-CN,zh;q=0.9',
        'referer': 'https://www.hifiti.com/sg_sign.htm',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    })

    r = session.get(url)
    name_element = r.html.find('a[href="my.htm"]', first=True)
    if name_element is None:
        return (f"{message}账号({i})无法登录！可能Cookie失效，请重新修改")

    wait_midnight()

    session.headers.update({
        'origin': url, 'referer': url,
        'accept': 'text/plain, */*; q=0.01',
        'x-requested-with': 'XMLHttpRequest',
    })
    p = session.post(f'{url}sg_sign.htm')
    if p.status_code == 200:
        write(signKey, today())
        message = p.json().get("message")
        r = session.get(url)
        message += f'\n当前{re.findall(r"连续签到.*?天", r.text)[0]}'
    session.headers.pop('X-Requested-With', None)

    f = session.get(f'{url}my-credits.htm')
    schedule = re.findall(r'<p>(用户组: .*?)</p>', f.text)[0]
    schedule += ' ' + f.html.find('div.progress', first=True).text
    matches = re.findall(r'(经验|金币|人民币).*?value="(\d+)"', f.text)
    res = ''.join([f'{match[0]}: {match[1]}\n' for match in matches])
    name = name_element.text.strip()
    return (f"--- {name} HIFITI 签到结果 ---\n{message}\n\n"
            f"<b>账户信息</b>\n{schedule}\n{res}")

def hifiti_main(check_items):
    msg_all = ''
    for i, item in enumerate(check_items, start=1):
        msg_all += f'{hifiti_sign(item.get("cookie"), i)}\n\n'
    return msg_all

if __name__ == "__main__":
    result = hifiti_main(get_data().get("HIFINI", []))
    if any(x in result for x in ['成功', '失败']):
        send("HIFITI 签到", result)
    else:
        print(result)
