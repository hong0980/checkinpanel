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
    message = "<b><span style='color: red'>签到失败</span></b>"
    session = HTMLSession()
    # setup_hooks(session, truncate=0)
    session.headers.update({'cookie': cookies})
    try:
        g = wait_midnight(
            wait=True, # 开启0点
            stime=1, retries=20, # 重试次数
            session=session, base_url=url
        ) or session.get(url)

        if not (name_element := g.html.find('a[href="my.htm"]', first=True)):
            return f"{message}\n账号({i})无法登录！可能Cookie失效，请重新修改"

        if (m := re.search(r"var s1 = '(.+?)'", g.text)) and '签到' in m.group(1):
                session.headers.update({
                    'origin': url, 'referer': url,
                    'x-requested-with': 'XMLHttpRequest',
                })
                p = session.post(f'{url}sg_sign.htm')
                if p.status_code == 200:
                    message = f'<b><span style="color: green">{p.json().get("message")}</span></b>'
                session.headers.pop('x-requested-with', None)

        name = name_element.text.strip()
        if '成功签到' in message:
            store.sleep(1)
            t = session.get(f'{url}sg_sign.htm')
            print(f'{url}sg_sign.htm', t.text)
            g = session.get(f'{url}sg_sign-list.htm')
            print(f'{url}sg_sign-list.htm', g.text)
            for row in g.html.find('tr'):
                tds = row.find('td')
                if tds and len(tds) >= 2:  # 至少要有用户名所在的td
                    if tds[1].text.strip() == name:
                        data = {
                            '排名': tds[0].text.strip(),
                            '用户名': tds[1].text.strip(),
                            '总奖励': tds[2].text.strip(),
                            '今日奖励': tds[3].text.strip(),
                            '签到时间': tds[4].text.strip(),
                            '签到天数': tds[5].text.strip(),
                            '连签天数': tds[6].text.strip()
                        }
                        print(f"找到用户 {name}: {data}")
                        break
            if store.mark_signed(signKey):
                print('签到记录成功')
            else:
                print('签到记录失败')
            if (m := re.search(r"var s3 = '(.+?)'", g.text)):
                message += f"\n当前{m.group(1)}"

        # for row in g.html.find('tr'):
        #     tds = row.find('td')
        #     if tds and len(tds) >= 7 and tds[1].text.strip() == name:
        #         keys = ['排名', '用户名', '总奖励', '今日奖励', '签到时间', '签到天数', '连签天数']
        #         data = {k: tds[i].text.strip() for i, k in enumerate(keys)}
        #         print(f"找到用户 {name}: {data}")
        #         break

        f = session.get(f'{url}my-credits.htm')
        schedule = f"{re.findall(r'<p>(用户组: .*?)</p>', f.text)[0]} {f.html.find('div.progress', first=True).text}"
        res = '\n'.join(f"{k}: {v}" for k, v in re.findall(r'(经验|金币|人民币).*?value=\"(\d+)\"', f.text)) + '\n'

        return (f"--- {name} HIFITI 签到结果 ---\n{store.now()}\n{message}\n\n"
                f"<b>账户信息</b>\n{schedule}\n{res}")

    except Exception as e:
        return f" 操作异常{str(e)}"

def main(check_items):
    msg_all = ''
    for i, item in enumerate(check_items, start=1):
        msg_all += f'{hifiti_sign(item.get("cookie"), i)}\n\n'
    return msg_all

if __name__ == "__main__":
    result = main(get_data().get("HIFINI", []))
    if re.search(r'成功|失败|登录|异常', result):
        send("HIFITI 签到", result)
    else:
        print(result)
    # print(result)
