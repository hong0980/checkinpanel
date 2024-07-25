# -*- coding: utf-8 -*-
"""
cron: 50 59 23 * * *
new Env('CHDBits 签到');
"""

import re
import time
import answers
from utils import get_data
from notify_mtr import send
from requests_html import HTMLSession
from datetime import datetime, timedelta

class Get:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        p, x, msg, res, cg_msg = None, '', '', '', ''
        url = 'https://ptchdbits.co/bakatest.php'
        headers = {
            "Cookie": cookie,
            'authority': 'ptchdbits.co',
            'origin': 'https://ptchdbits.co',
            'referer': 'https://ptchdbits.co/bakatest.php',
        }

        def countdown():
            now = datetime.now()
            if now.hour == 23 and 57 <= now.minute <= 59:
                midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                sleep_seconds = (midnight - now).total_seconds()
                print(f'等待{int(sleep_seconds)}秒后执行签到！')
                time.sleep(sleep_seconds)

        def check_answer_values(value):
            valid_values = {'1', '2', '4', '8'}
            return not ((isinstance(value, str) and value in valid_values) \
                   or (isinstance(value, list) and set(value).issubset(valid_values)))

        def generate_answer(r, value):
            if value:
                match = re.search(rf"<input[^>]*value='(\d+)'[^>]*>[^<]*{re.escape(value)}", r.text)
                if match:
                    return match.group(1)

            from random import choice, sample
            values = re.findall(r"name='choice.*?value='(\d+)'", r.text)
            random_value = choice(values)
            if '多选' in r.text:
                remaining_values = [v for v in values if v != random_value]
                return sample(remaining_values, 2) if remaining_values else ['']
            else:
                return random_value

        try:
            with HTMLSession() as s:
                countdown()
                r = s.get(url, headers={"Cookie": cookie}, timeout=10)
                if '欢迎回来' not in r.text:
                    return f'账号({i})无法登录！可能Cookie失效，请重新修改'

                if '今天已经签过到了' in r.text:
                    qd_msg = re.findall(r'<font color="white">(.*?签到.*?)</font>', r.text)[0]
                else:
                    question_id = re.findall(r'name="questionid" value="(\d+)"', r.text)[0]
                    answer = answers.get(question_id)
                    if not answer or check_answer_values(answer):
                        x = 1 if answer else 2
                        answer = generate_answer(r, answer)

                    data = {
                        'choice[]': answer,
                        'questionid': question_id,
                        'usercomment': '此刻心情:无',
                        'wantskip': '不会',
                    }
                    p = s.post(url, headers=headers, data=data)

                    now_time = datetime.now().time()
                    question = re.findall(r'\](\[.*?选\]).*?请问：(.*?)</td></tr>', r.text)[0]
                    form_tag = r.html.find('form', first=True)
                    question_text = form_tag.find('td')[1].text.strip()
                    msg = f'<b>题目 {question_id}</b>\n选择题{question[0]}：{question[1]}\n{question_text}\n\n<b>使用数值答案</b>\n'
                    if x:
                        h = '使用题目答案'
                        if x == 2:
                            h = '使用随机答案'
                        msg = f'<b>题目 {question_id}</b>\n选择题{question[0]}：{question[1]}\n{question_text}\n\n<b><span style="color: red">{h}：{answer}</span></b>\n'
                        tr_tags = form_tag.find('tr')[:2]
                        with open('/tmp/chdbits_非数值答案题目.html.txt', 'a', encoding='utf-8') as file:
                            for tr in tr_tags:
                                file.write(tr.html + '\n')
                            file.write('\n')

                    for values in answer:
                        question_text = re.findall(rf"value='{values}'\s*>(.*?)<", r.text, re.DOTALL)[0]
                        question_text = re.sub(r"&nbsp;|&quot;", '', question_text)
                        msg += f'{question_text}\n'
                    msg += '\n'
                    qd_msg = re.findall(r'<font color="white">(.*?签到.*?)</font>', p.text)[0]
                    dt = re.findall(r"title='(.*?)'\s*>(\d+)</td>", p.text)
                    dt = sorted(set(dt), key=lambda x: int(x[1]))
                    for match in dt:
                        if not answers.check_key(match[1]):
                            print(f"'{match[1]}': '',  # {match[0]}")

                    if '获得' in qd_msg:
                        with open('/tmp/chdbits_成功.html.txt', 'w', encoding='utf-8') as file:
                            file.write(p.html.html)
                        cg_msg = f"<b><span style='color: green'>签到成功</span></b> {now_time}\n"
                    else:
                        cg_msg = "CHDBits 签到失败"

                name = re.findall(r"class='UltimateUser_Name'><b>(.*?)</b>", r.text, re.DOTALL)[0]
                res = f"--- {name} CHDBits 签到结果 ---\n{cg_msg}"
                res += f"<b><span style='color: {'purple' if '签过到了' in qd_msg else 'orange'}'>{qd_msg}</span></b>\n\n"
                pattern = r'使用</a>]: (.*?)\s*<font.*?分享率：</font>\s*(.*?)\s*<font.*?上传量：</font>\s*(.*?)\s*<font.*?下载量：</font>\s*(.*?)\s*<font.*?当前做种.*?>\s*(\d+)\s*<img.*?做种积分: </font>(.*?)</span>'
                text_to_search = p.text if p else r.text if r else ''
                result = re.findall(pattern, text_to_search, re.DOTALL)[0]
                res += (f'{msg}<b>账户信息</b>\n'
                       f'魔力值：{result[0]}\n'
                       f'分享率：{result[1]}\n'
                       f'上传量：{result[2]}\n'
                       f'下载量：{result[3]}\n'
                       f'当前做种：{result[4]}\n'
                       f'做种积分：{result[5]}'
                )

        except Exception as e:
            res = f"发生异常: {e}"
        except requests.RequestException as e:
            res = f"请求发生错误: {e}"
        finally:
            session.close()
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            sign_msg = self.sign(cookie, i)
            msg = f"{sign_msg}"
            msg_all += msg + "\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("CHDBITS", [])
    result = Get(check_items=_check_items).main()
    send("CHDBits 签到信息", result)
    # print(result)
