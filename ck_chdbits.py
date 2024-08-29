# -*- coding: utf-8 -*-
"""
cron: 55 59 11,23 * * *
new Env('CHDBits 签到');
"""

import re, sys, time
try:
    import answers
except ImportError:
    sys.exit(1)
from utils import get_data
from notify_mtr import send
from requests_html import HTMLSession
from datetime import datetime, timedelta

class Get:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        def check_answer_values(value):
            return not ((isinstance(value, str) and value in valid_values) \
                   or (isinstance(value, list) and all(v in valid_values for v in value)))

        def generate_answer(r, value):
            if value:
                match = re.findall(rf"value='(\d+)'\s*>[^<]*{re.escape(value)}", r.text)
                if match:
                    return match[0]

            from random import choice, sample
            if '[多选]' in r.text:
                return sample(valid_values, 3)
            return choice(valid_values)

        p, x, msg, cg_msg, now, g, url, valid_values = '', '', '', '', datetime.now(), \
        '使用数值答题', 'https://ptchdbits.co/bakatest.php', ('1', '2', '4', '8')
        headers = {'referer': url, 'authority': 'ptchdbits.co',
                   'Cookie': cookie, 'origin': 'https://ptchdbits.co'}

        try:
            with HTMLSession(executablePath='/usr/bin/chromium') as s:
                if now.hour == 23 and 57 <= now.minute <= 59:
                    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                    sleep_seconds = (midnight - now).total_seconds()
                    print(f'等待{int(sleep_seconds)}秒后执行签到！')
                    time.sleep(sleep_seconds)

                r = s.get(url, headers=headers)
                question_id = r.html.search('name="questionid" value="{}"')
                question_id = question_id[0] if question_id else None
                if question_id is None:
                    return (f"<b><span style='color: red'>签到失败</span></b>\n"
                            f"账号({i})无法登录！可能Cookie失效，请重新修改")

                qd_msg = re.findall(r'white">(.*?签到.*?)<', r.text)
                if not '签过到了' in r.text:
                    answer = answers.get(question_id)
                    if not answer or check_answer_values(answer):
                        x = 1 if answer else 2
                        answer = generate_answer(r, answer)

                    data = {'choice[]': answer, 'questionid': question_id,
                            'wantskip': '不会', 'usercomment': '此刻心情:无'}
                    p = s.post(url, headers=headers, data=data)
                    now_time = datetime.now().time()
                    question = re.findall(r'](\[.选\])\s*?请问：(.*?)</td>', r.text)[0]
                    table_tag = r.html.find('table[border="1"]', first=True)
                    question_text = table_tag.find('td')[1].text.strip()
                    msg = (f'<b><span style="color: orange">题目 {question_id}</span></b>\n'
                           f'{question[0]}：{question[1]}\n{question_text}\n\n')
                    if x:
                        g = f'{"使用题目答题" if x == 1 else "使用随机答题"}：{answer}'
                        tr_tags = table_tag.find('tr')[:2]
                        with open('/tmp/chdbits_非数值答案题目.html.txt', 'a', encoding='utf-8') as file:
                            for tr in tr_tags:
                                file.write(tr.html + '\n')
                            file.write('\n')

                    msg += f"<b><span style='color: {'orange' if '数值' in g else 'red'}'>{g}</span></b>\n"
                    for values in answer:
                        question_text = re.findall(rf"value='{values}'\s*>(.*?)<", r.text, re.DOTALL)[0]
                        question_text = re.sub(r"&nbsp;|&quot;", '', question_text)
                        msg += f'{question_text}\n'
                    msg += '\n'

                    qd_msg = re.findall(r'white">(.*?签到.*?)<', p.text)
                    if '获得' in qd_msg[0]:
                        cg_msg = f"<b><span style='color: green'>签到成功</span></b> {now_time}\n"
                        with open('/tmp/chdbits_成功.html.txt', 'w', encoding='utf-8') as file:
                            file.write(p.html.html)
                    elif not '签过到了' in qd_msg[0]:
                        cg_msg = "<b><span style='color: red'>签到失败</span></b>\n"

                pattern = (r"UltimateUser_Name'><b>(.*?)</b>.*?"
                           r'使用</a>]:\s*?(.*?)\s*?<.*?'
                           r'分享率：</font>\s*?(.*?)\s*?<.*?'
                           r'上传量：</font>\s*?(.*?)\s*?<.*?'
                           r'下载量：</font>\s*?(.*?)\s*?<.*?'
                           r'当前做种.*?(\d+).*?<.*?'
                           r'做种积分: </font>\s*?(.*?)<')
                text_search = p.text if p else r.text
                result = re.findall(pattern, text_search, re.DOTALL)[0]
                res = (f"--- {result[0]} CHDBits 签到结果 ---\n{cg_msg}<b><span style='color: "
                       f"{'purple' if '签过到了' in qd_msg[0] else 'orange'}'>{qd_msg[0]}</span></b>\n\n"
                       f'{msg}<b><span style="color: orange">账户信息</span></b>\n'
                       f'魔力值：{result[1]}\n分享率：{result[2]}\n'
                       f'上传量：{result[3]}\n下载量：{result[4]}\n'
                       f'当前做种：{result[5]}\n做种积分：{result[6]}')

                for matchs in re.findall(r"title='(.*?)'\s*>(\d+)</td>", text_search):
                    if not answers.check_key(matchs[1]):
                        f = f"'{matchs[1]}': '',  # {matchs[0]}"
                        print(f)
                        with open('/tmp/chdbits_题目.txt', 'a', encoding='utf-8') as file:
                            file.write(f + '\n')

        except Exception:
            import traceback
            return f"<b><span style='color: red'>未知异常：</span></b>\n{traceback.format_exc()}"
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            msg_all += f'{self.sign(cookie, i)}\n\n'
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("CHDBITS", [])
    result = Get(check_items=_check_items).main()
    if '获得' in result:
        send("CHDBits 签到", result)
    else:
        print(result)
