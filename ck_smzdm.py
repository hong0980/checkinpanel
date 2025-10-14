"""
cron: 39 8,17 * * *
new Env('什么值得买 签到')
"""
import requests.exceptions
from notify_mtr import send
from datetime import datetime
import time, hashlib, random, re
from requests_html import HTMLSession
from utils import get_data, store

def get_user_info(session):
    try:
        infourl = 'https://zhiyou.smzdm.com/user/'
        session.headers.update({
            'Host': 'zhiyou.smzdm.com',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
            'Referer': 'https://m.smzdm.com/',
            'Accept-Encoding': 'gzip, deflate, br'
        })

        response_info = session.get(url=infourl, timeout=15).text

        name_match = re.search(r'<a href="https://zhiyou.smzdm.com/user"> (.*?) </a>', response_info)
        level_match = re.search(r'<img src=".*?/level/(\d+).png.*?"', response_info)
        gold_match = re.search(r'<div class="assets-part assets-gold">.*?<span class="assets-part-element assets-num">(.*?)</span>', response_info, re.S)
        silver_match = re.search(r'<div class="assets-part assets-prestige">.*?<span class="assets-part-element assets-num">(.*?)</span>', response_info, re.S)

        name = name_match.group(1).strip() if name_match else "未知用户"
        level = level_match.group(1) if level_match else "0"
        gold = gold_match.group(1).strip() if gold_match else "0"
        silver = silver_match.group(1).strip() if silver_match else "0"

        return name, level, gold, silver
    except Exception as e:
        print(f" 获取用户信息失败: {e}")
        return "未知用户", "0", "0", "0"

def get_monthly_exp(session):
    try:
        current_month = datetime.now().strftime('%Y-%m')
        total_exp = 0

        for page in range(1, 4):  # 查询前3页
            url = f'https://zhiyou.m.smzdm.com/user/exp/ajax_log?page={page}'
            session.headers.update({
                'Host': 'zhiyou.m.smzdm.com',
                'Accept': 'application/json, text/plain, */*',
                'Referer': 'https://zhiyou.m.smzdm.com/user/exp/',
            })

            resp = session.get(url=url, timeout=10)
            if resp.status_code != 200:
                break

            result = resp.json()
            rows = result.get('data', {}).get('rows', [])

            if not rows:
                break

            for row in rows:
                exp_date = row.get('creation_date', '')[:7]
                if exp_date == current_month:
                    total_exp += int(row.get('add_exp', 0))
                elif exp_date < current_month:
                    # 如果日期小于当前月份，说明已经查完了
                    return total_exp

            time.sleep(random.uniform(0.5, 1.5))
        return total_exp
    except Exception as e:
        print(f" 获取月度经验失败: {e}")
        return 0

def sign_in(cookie, i):
    signKey = f"smzdm_sign_{i}"
    if store.read(signKey) == store.today():
        return (f"账号 {i}: ✅ 今日已签到")

    session = HTMLSession()
    try:
        ts = int(round(time.time() * 1000))
        url = 'https://user-api.smzdm.com/robot/token'
        session.headers.update({
            'Host': 'user-api.smzdm.com',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookie,
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148/smzdm 10.4.40 rv:137.6 (iPhone 13; iOS 15.6; zh_CN)/iphone_smzdmapp/10.4.40/wkwebview/jsbv_1.0.0',
        })
        data = {
            "f": "android", "v": "10.4.1", "weixin": 1, "time": ts,
            "sign": hashlib.md5(bytes(f'f=android&time={ts}&v=10.4.1&weixin=1&key=apr1$AwP!wRRT$gJ/q.X24poeBInlUJC', encoding='utf-8')).hexdigest().upper()
        }
        result = session.post(url=url, data=data, timeout=15).json()
        token = result['data']['token']
        if not token:
            return '登录失败'

        Timestamp = int(round(time.time() * 1000))
        sign_data = {
            "f": "android", "v": "10.4.1", "weixin": 1, "time": Timestamp, "token": token,
            "sk": "ierkM0OZZbsuBKLoAgQ6OJneLMXBQXmzX+LXkNTuKch8Ui2jGlahuFyWIzBiDq/L",
            "sign": hashlib.md5(bytes(f'f=android&sk=ierkM0OZZbsuBKLoAgQ6OJneLMXBQXmzX+LXkNTuKch8Ui2jGlahuFyWIzBiDq/L&time={Timestamp}&token={token}&v=10.4.1&weixin=1&key=apr1$AwP!wRRT$gJ/q.X24poeBInlUJC', encoding='utf-8')).hexdigest().upper()
        }

        url_signin = 'https://user-api.smzdm.com/checkin'
        html_signin = session.post(url=url_signin, data=sign_data, timeout=15)

        signin_result = html_signin.json()
        signin_msg = signin_result.get('error_msg', '签到状态未知')
        signin_code = signin_result.get('error_code', -1)

        url_reward = 'https://user-api.smzdm.com/checkin/all_reward'
        html_reward = session.post(url=url_reward, data=sign_data, timeout=15)

        reward_info = ""
        if html_reward.status_code == 200:
            try:
                reward_result = html_reward.json()
                if str(reward_result.get('error_code')) == "0" and reward_result.get('data'):
                    normal_reward = reward_result["data"].get("normal_reward", {})
                    if normal_reward:
                        reward_content = normal_reward.get("reward_add", {}).get("content", "无奖励")
                        sub_title = normal_reward.get("sub_title", "无连续签到信息")
                        reward_info = f"\n 签到奖励: {reward_content}\n📅 连续签到: {sub_title}"
            except Exception as e:
                print(f" 奖励信息解析失败: {e}")
        else:
            print(f" 奖励查询失败，状态码: {html_reward.status_code}")

        monthly_exp = get_monthly_exp(session)
        name, level, gold, silver = get_user_info(session)
        msg = f"----账号 {i} {name} 什么值得买 签到状态 ----\n"
        msg += '\n'.join([
            f'等级: VIP{level}',
            f'金币: {gold}',
            f'碎银: {silver}',
            f'本月经验: {monthly_exp}',
            f'签到状态: {signin_msg}',
            (reward_info or '')
        ])

        is_success = (str(signin_code) == "0" or
                     "成功" in signin_msg or
                     "已经" in signin_msg or
                     "重复" in signin_msg or
                     "已签" in signin_msg)

        if is_success:
            store.write(signKey, store.today())
        return msg

    except requests.exceptions.Timeout:
        return f" 账号{i}: 请求超时，网络连接可能有问题"
    except requests.exceptions.ConnectionError:
        return f" 账号{i}: 网络连接错误，无法连接到服务器"
    except Exception as e:
        return f" 账号{i}: 签到异常 - {str(e)}"
    finally:
        session.close()

def main(account):
    msg_all = ""
    for idx, acc in enumerate(account, 1):
        msg = sign_in(acc.get("cookie"), idx)
        msg_all += msg + "\n\n"
    return msg_all

if __name__ == "__main__":
    result = main(get_data().get("SMZDM", []))
    if re.search(r'成功|失败|异常|错误|登录', result):
        send("什么值得买 签到", result)
    else:
        print(result)
