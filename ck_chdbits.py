# -*- coding: utf-8 -*-
"""
cron: 55 57 8,15,23 * * *
new Env('CHDBits 签到');
"""

import re, sys
try:
    import answers
except ImportError:
    sys.exit(1)
from notify_mtr import send
from random import choice, sample
from fake_useragent import UserAgent
from requests_html import HTMLSession
from utils import get_data, now, today, read, write, wait_midnight

class CHDBits:
    def __init__(self, check_items):
        self.session = HTMLSession()
        self.check_items = check_items

    def sign_in(self, cookie, i):
        signKey = f"chdbits_sign_{i}"
        if read(signKey) == today(tomorrow_if_late=True):
            return (f"账号 {i}: ✅ 今日已签到")

        def is_valid_answer(value):
            return value in valid_values if isinstance(value, str) else \
                   any(item in valid_values for item in value) if isinstance(value, list) else False

        def generate_answer(html_content, answer_value):
            if match := re.findall(rf"value='(\d+)'\s*>[^<]*{answer_value}", html_content):
                return match[0]
            return sample(valid_values, 3) if '[多选]' in html_content else choice(valid_values)

        answer_source = None
        answer_method = '使用数值答题'
        valid_values = ('1', '2', '4', '8')
        base_url = 'https://ptchdbits.co/bakatest.php'
        sign_in_result = "<b><span style='color: red'>签到失败</span></b>\n"

        self.session.headers.update({
            'Cookie': cookie, 'Referer': base_url, 'User-Agent': UserAgent().chrome,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })

        wait_midnight(session=self.session, base_url=base_url, offset=60, wait=True, stime=2)
        get_response = self.session.get(base_url)

        try:
            if not (question_id := get_response.html.find('input[name=questionid]', first=True).attrs.get('value')):
                return f"{sign_in_result}账号({i})无法登录！可能Cookie失效"

            selected_answers = answers.get(question_id)
            if not (selected_answers and is_valid_answer(selected_answers)):
                answer_source = 1 if selected_answers else 2
                selected_answers = generate_answer(get_response.text, selected_answers)

            data = {
                'questionid': question_id, 'choice[]': selected_answers,
                'usercomment': '此刻心情:无', 'wantskip': '不会'
            }

            self.session.headers.update({
                'Origin': 'https://ptchdbits.co',
                'Content-Type': 'application/x-www-form-urlencoded'
            })
            current_now = now()
            post_response = self.session.post(base_url, data=data)
            sign_in_message = re.findall(r'white">(.*?签到.*?)<', post_response.text)[0]
            if '获得' in sign_in_message:
                sign_in_result = f"<b><span style='color: green'>签到成功</span></b>  {current_now}\n"
                with open('/ql/data/log/chdbits_成功.html.txt', 'w', encoding='utf-8') as f:
                    f.write(post_response.html.html)
            elif '签过到了' in sign_in_message:
                sign_in_result = ""

            question_info = re.findall(r'](\[.选\])\s*?请问：(.*?)</td>', get_response.text)[0]
            question_table = get_response.html.find('table[border="1"]', first=True)
            question_text = question_table.find('td')[1].text.strip()

            if answer_source:
                answer_method = f'{"使用题目答题" if answer_source == 1 else "使用随机答题"}：{selected_answers}'
                with open('/ql/data/log/chdbits_非数值答案题目.html.txt', 'a', encoding='utf-8') as f:
                    f.write('\n'.join(row.html for row in question_table.find('tr')[:2]) + '\n\n')
            topic = (f'<b><span style="color: orange">题目 {question_id}</span></b>\n'
                     f'{question_info[0]}：{question_info[1]}\n{question_text}\n\n')
            topic += f"<b><span style='color: {'orange' if '数值' in answer_method else 'red'}'>{answer_method}</span></b>\n"
            topic += '\n'.join(
                re.sub(r"&nbsp;|&quot;", '',
                re.findall(rf"value='{v}'\s*>(.*?)<", get_response.text, re.DOTALL)[0])
                for v in selected_answers
            ) + '\n\n'

            user_info = re.findall(
                r"UltimateUser_Name'><b>(.*?)</b>.*?"
                r'使用</a>]:\s*?(.*?)\s*?<.*?'
                r'分享率：</font>\s*?(.*?)\s*?<.*?'
                r'上传量：</font>\s*?(.*?)\s*?<.*?'
                r'下载量：</font>\s*?(.*?)\s*?<.*?'
                r'当前做种.*?(\d+).*?<.*?'
                r'做种积分: </font>\s*?(.*?)<',
                post_response.text, re.DOTALL
            )[0]
            if re.search(r'成功|签过到了', sign_in_message):
                write(signKey, today())

            return (
                f"--- {user_info[0]} CHDBits 签到结果 ---\n{sign_in_result}"
                f"<b><span style='color: orange'>{sign_in_message}</span></b>\n\n"
                f"{topic}<b><span style='color: orange'>账户信息</span></b>\n"
                f"魔力值：{user_info[1]}\n分享率：{user_info[2]}\n"
                f"上传量：{user_info[3]}\n下载量：{user_info[4]}\n"
                f"当前做种：{user_info[5]}\n做种积分：{user_info[6]}"
            )

        except Exception:
            import traceback
            return f"<b><span style='color: red'>未知异常：</span></b>\n{traceback.format_exc()}"

    def main(self):
        return "\n\n".join(
            self.sign_in(account.get("cookie"), idx)
            for idx, account in enumerate(self.check_items, 1)
        )

if __name__ == "__main__":
    result = CHDBits(get_data().get("CHDBITS", [])).main()
    if any(x in result for x in ['签到成功', '签到失败', '未知异常']):
        send("CHDBits 签到", result)
    else:
        print(result)
