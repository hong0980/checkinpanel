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
            if isinstance(value, str):
                return value in valid_values
            if isinstance(value, list):
                return any(i in valid_values for i in value)
            return False

        def generate_answer(html, value):
            if value:
                if match := re.findall(rf"value='(\d+)'\s*>[^<]*{re.escape(value)}", html):
                    return match[0]

            from random import choice, sample
            return sample(valid_values, 3) if '[多选]' in html else choice(valid_values)

        valid_values = ('1', '2', '4', '8')
        p, x, msg, cg_msg = None, '', '', ''
        s, now = HTMLSession(), datetime.now()
        url = 'https://ptchdbits.co/bakatest.php'
        s.headers.update({
            'authority': 'ptchdbits.co', 'Cookie': cookie,
            'origin': 'https://ptchdbits.co', 'referer': url
        })

        if now.hour == 23 and 57 <= now.minute <= 59:
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            sleep_seconds = (midnight - now).total_seconds()
            print(f'等待{int(sleep_seconds)}秒后执行签到！')
            time.sleep(sleep_seconds)

        try:
            r = s.get(url)
            if not (question_id := r.html.find('input[name=questionid]', first=True).attrs.get('value')):
                return f"<b><span style='color: red'>签到失败</span></b>\n账号({i})无法登录！可能Cookie失效，请重新修改"

            if not '签过到了' in r.text:
                answer_values = answers.get(question_id)
                if not (answer_values and check_answer_values(answer_values)):
                    x = 1 if answer_values else 2
                    answer_values = generate_answer(r.text, answer_values)

                data = {
                    'wantskip': '不会', 'usercomment': '此刻心情:无',
                    'choice[]': answer_values, 'questionid': question_id
                }
                now_time = datetime.now().time()
                p = s.post(url, data=data)
                question = re.findall(r'](\[.选\])\s*?请问：(.*?)</td>', r.text)[0]
                table_tag = r.html.find('table[border="1"]', first=True)
                question_text = table_tag.find('td')[1].text.strip()
                msg = (f'<b><span style="color: orange">题目 {question_id}</span></b>\n'
                       f'{question[0]}：{question[1]}\n{question_text}\n\n')
                g = '使用数值答题'
                if x:
                    g = f'{"使用题目答题" if x == 1 else "使用随机答题"}：{answer_values}'
                    tr_tags = table_tag.find('tr')[:2]
                    with open('/tmp/chdbits_非数值答案题目.html.txt', 'a', encoding='utf-8') as file:
                        for tr in tr_tags:
                            file.write(tr.html + '\n')
                        file.write('\n')

                msg += f"<b><span style='color: {'orange' if '数值' in g else 'red'}'>{g}</span></b>\n"
                for values in answer_values:
                    question_text = re.findall(rf"value='{values}'\s*>(.*?)<", r.text, re.DOTALL)[0]
                    question_text = re.sub(r"&nbsp;|&quot;", '', question_text)
                    msg += f'{question_text}\n'
                msg += '\n'

            pattern = (r"UltimateUser_Name'><b>(.*?)</b>.*?"
                       r'使用</a>]:\s*?(.*?)\s*?<.*?'
                       r'分享率：</font>\s*?(.*?)\s*?<.*?'
                       r'上传量：</font>\s*?(.*?)\s*?<.*?'
                       r'下载量：</font>\s*?(.*?)\s*?<.*?'
                       r'当前做种.*?(\d+).*?<.*?'
                       r'做种积分: </font>\s*?(.*?)<')
            text_search = p.text if p else r.text
            qd_msg = re.findall(r'white">(.*?签到.*?)<', text_search)
            if '获得' in qd_msg[0]:
                cg_msg = f"<b><span style='color: green'>签到成功</span></b> {now_time}\n"
                with open('/tmp/chdbits_成功.html.txt', 'w', encoding='utf-8') as file:
                    file.write(p.html.html)
            elif not '签过到了' in qd_msg[0]:
                cg_msg = "<b><span style='color: red'>签到失败</span></b>\n"

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
    result = Get(check_items=get_data().get("CHDBITS", [])).main()
    if '获得' in result or '签到失败' in result or '请求失败' in result:
        send("CHDBits 签到", result)
    else:
        print(result)
