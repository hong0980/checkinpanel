# -*- coding: utf-8 -*-
"""
cron: 55 59 23 * * *
new Env('CHDBits 签到');
"""

import re, sys, time
try:
    import answers
except ImportError:
    print("无法导入 'answers' 模块，退出。")
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
        def countdown():
            now = datetime.now()
            if now.hour == 23 and 57 <= now.minute <= 59:
                midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                sleep_seconds = (midnight - now).total_seconds()
                print(f'等待{int(sleep_seconds)}秒后执行签到！')
                time.sleep(sleep_seconds)

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

        valid_values = ('1', '2', '4', '8')
        p, x, msg, res, cg_msg = None, '', '', '', ''
        url = 'https://ptchdbits.co/bakatest.php'
        headers = {'referer': url, 'Cookie': cookie,
                   'authority': 'ptchdbits.co',
                   'origin': 'https://ptchdbits.co'}

        try:
            with HTMLSession(executablePath='/usr/bin/chromium') as s:
                countdown()
                r = s.get(url, headers=headers)
                question_id = r.html.search('name="questionid" value="{}"')
                question_id = question_id[0] if question_id else None
                if question_id is None:
                    return f'账号({i})无法登录！可能Cookie失效，请重新修改'

                if '签过到了' in r.text:
                    qd_msg = re.findall(r'<font color="white">(.*?签到.*?)</font>', r.text)[0]
                else:
                    answer = answers.get(question_id)
                    if not answer or check_answer_values(answer):
                        x = 1 if answer else 2
                        answer = generate_answer(r, answer)

                    data = {'choice[]': answer,
                            'wantskip': '不会',
                            'questionid': question_id,
                            'usercomment': '此刻心情:无'}
                    p = s.post(url, headers=headers, data=data)

                    now_time = datetime.now().time()
                    question = re.findall(r'\](\[.选\])\s*请问：(.*?)</td>', r.text)[0]
                    table_tag = r.html.find('table[border="1"]', first=True)
                    question_text = table_tag.find('td')[1].text.strip()
                    msg = (f'<b><span style="color: orange">题目 {question_id}</span></b>\n'
                           f'{question[0]}：{question[1]}\n{question_text}\n\n')
                    g = '使用数值答题'
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
                    matche = re.findall(r"title='(.*?)'\s*>(\d+)</td>", p.text)
                    matche = sorted(matche, key=lambda x: int(x[1]))
                    for matchs in matche:
                        if not answers.check_key(matchs[1]):
                            print(f"'{matchs[1]}': '',  # {matchs[0]}")

                    qd_msg = re.findall(r'<font color="white">(.*?签到.*?)</font>', p.text)[0]
                    if '获得' in qd_msg:
                        cg_msg = f"<b><span style='color: green'>签到成功</span></b> {now_time}\n"
                        with open('/tmp/chdbits_成功.html.txt', 'w', encoding='utf-8') as file:
                            file.write(p.html.html)
                    elif not '签过到了' in qd_msg:
                        cg_msg = "<b><span style='color: red'>签到失败</span></b>\n"

                pattern = (r'UltimateUser_Name\'><b>(.*?)</b>.*?'
                           r'使用</a>]: (.*?)\s*'
                           r'<font.*?分享率：</font>\s*(.*?)\s*'
                           r'<font.*?上传量：</font>\s*(.*?)\s*'
                           r'<font.*?下载量：</font>\s*(.*?)\s*'
                           r'<font.*?当前做种.*?(\d+).*?<font.*?'
                           r'做种积分: </font>\s*(.*?)</')
                text_search = p.text if p else r.text
                result = re.findall(pattern, text_search, re.DOTALL)[0]
                res = f"--- {result[0]} CHDBits 签到结果 ---\n{cg_msg}"
                res += f"<b><span style='color: {'purple' if '签过到了' in qd_msg else 'orange'}'>{qd_msg}</span></b>\n\n"
                res += (f'{msg}<b><span style="color: orange">账户信息</span></b>\n'
                        f'魔力值：{result[1]}\n'
                        f'分享率：{result[2]}\n'
                        f'上传量：{result[3]}\n'
                        f'下载量：{result[4]}\n'
                        f'当前做种：{result[5]}\n'
                        f'做种积分：{result[6]}')

        except Exception as e:
            res = f"发生异常: {e}"
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
    send("CHDBits 签到", result)
    # print(result)
