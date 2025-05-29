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
    def sign_in(cookie, account_index):
        def is_valid_answer(value):
            if isinstance(value, str):
                return value in valid_values
            if isinstance(value, list):
                return any(item in valid_values for item in value)
            return False

        def generate_answer(html_content, answer_value):
            if match := re.findall(rf"value='(\d+)'\s*>[^<]*{answer_value}", html_content):
                return match[0]

            from random import choice, sample
            return sample(valid_values, 3) if '[多选]' in html_content else choice(valid_values)

        post_response, answer_source, message, sign_in_result, wait_seconds = None, '', '', '', ''
        session, current_time, valid_values = HTMLSession(), datetime.now(), ('1', '2', '4', '8')
        base_url = 'https://ptchdbits.co/bakatest.php'
        session.headers.update({
            'authority': 'ptchdbits.co', 'Cookie': cookie,
            'origin': 'https://ptchdbits.co', 'referer': base_url
        })

        if current_time.hour == 23 and 57 <= current_time.minute <= 59:
            midnight = current_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            wait_seconds = (midnight - current_time).total_seconds() + 45
            print(f'等待{int(wait_seconds)}秒后执行签到！')
            time.sleep(wait_seconds)

        try:
            response = session.get(base_url)
            if not (question_id := response.html.find('input[name=questionid]', first=True).attrs.get('value')):
                return f"<b><span style='color: red'>签到失败</span></b>\n账号({account_index})无法登录！可能Cookie失效，请重新修改"

            if not '签过到了' in response.text:
                selected_answers = answers.get(question_id)
                if not (selected_answers and is_valid_answer(selected_answers)):
                    answer_source = 1 if selected_answers else 2
                    selected_answers = generate_answer(response.text, selected_answers)

                action_button = '不会' if wait_seconds else '提交'
                form_data = {
                    'questionid': question_id, 'choice[]': selected_answers,
                    'usercomment': '此刻心情:无', 'submit': action_button,
                }
                current_time_of_day = datetime.now().time()
                post_response = session.post(base_url, data=form_data)
                question_info = re.findall(r'](\[.选\])\s*?请问：(.*?)</td>', response.text)[0]
                question_table = response.html.find('table[border="1"]', first=True)
                question_text = question_table.find('td')[1].text.strip()
                message = (f'<b><span style="color: orange">题目 {question_id}</span></b>\n'
                          f'{question_info[0]}：{question_info[1]}\n{question_text}\n\n')
                answer_method = '使用数值答题'
                if answer_source:
                    answer_method = f'{"使用题目答题" if answer_source == 1 else "使用随机答题"}：{selected_answers}'
                    table_rows = question_table.find('tr')[:2]
                    with open('/ql/data/log/chdbits_非数值答案题目.html.txt', 'a', encoding='utf-8') as file:
                        for row in table_rows:
                            file.write(row.html + '\n')
                        file.write('\n')

                message += f"<b><span style='color: {'orange' if '数值' in answer_method else 'red'}'>{answer_method}</span></b>\n"
                for value in selected_answers:
                    option_text = re.findall(rf"value='{value}'\s*>(.*?)<", response.text, re.DOTALL)[0]
                    option_text = re.sub(r"&nbsp;|&quot;", '', option_text)
                    message += f'{option_text}\n'
                message += '\n'

            response_text = post_response.text if post_response else response.text
            sign_in_message = re.findall(r'white">(.*?签到.*?)<', response_text)[0]
            if '获得' in sign_in_message:
                sign_in_result = f"<b><span style='color: green'>签到成功</span></b> {current_time_of_day}\n"
                with open('/ql/data/log/chdbits_成功.html.txt', 'w', encoding='utf-8') as file:
                    file.write(post_response.html.html)
            elif not '签过到了' in sign_in_message:
                sign_in_result = "<b><span style='color: red'>签到失败</span></b>\n"

            info_pattern = (r"UltimateUser_Name'><b>(.*?)</b>.*?"
                           r'使用</a>]:\s*?(.*?)\s*?<.*?'
                           r'分享率：</font>\s*?(.*?)\s*?<.*?'
                           r'上传量：</font>\s*?(.*?)\s*?<.*?'
                           r'下载量：</font>\s*?(.*?)\s*?<.*?'
                           r'当前做种.*?(\d+).*?<.*?'
                           r'做种积分: </font>\s*?(.*?)<')
            user_info = re.findall(info_pattern, response_text, re.DOTALL)[0]
            result = (f"--- {user_info[0]} CHDBits 签到结果 ---\n{sign_in_result}<b><span style='color: "
                     f"{'purple' if '签过到了' in sign_in_message else 'orange'}'>{sign_in_message}</span></b>\n\n"
                     f'{message}<b><span style="color: orange">账户信息</span></b>\n'
                     f'魔力值：{user_info[1]}\n分享率：{user_info[2]}\n'
                     f'上传量：{user_info[3]}\n下载量：{user_info[4]}\n'
                     f'当前做种：{user_info[5]}\n做种积分：{user_info[6]}')

            for match in re.findall(r"title='(.*?)'\s*>(\d+)</td>", response_text):
                if not answers.check_key(match[1]):
                    log_entry = f"'{match[1]}': '',  # {match[0]}"
                    print(log_entry)
                    with open('/ql/data/log/chdbits_未添加题目.txt', 'a', encoding='utf-8') as file:
                        file.write(log_entry + '\n')

        except Exception:
            import traceback
            return f"<b><span style='color: red'>未知异常：</span></b>\n{traceback.format_exc()}"
        return result

    def main(self):
        all_messages = ""
        for index, account_config in enumerate(self.check_items, start=1):
            cookie = account_config.get("cookie")
            all_messages += f'{self.sign_in(cookie, index)}\n\n'
        return all_messages

if __name__ == "__main__":
    result = Get(check_items=get_data().get("CHDBITS", [])).main()
    if '获得' in result or '签到失败' in result or '请求失败' in result:
        send("CHDBits 签到", result)
    else:
        print(result)
