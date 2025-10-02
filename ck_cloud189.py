# -*- coding: utf-8 -*-
"""
cron: 10 0,13 * * *
new Env('天翼云盘');
"""

from datetime import datetime
from notify_mtr import send
import base64, re, time, rsa
from requests_html import HTMLSession
from utils import today, read, write, now, get_data, setup_hooks

class Cloud189:
    def __init__(self, check_items, use_hooks=False):
        self.session = HTMLSession()
        self.check_items = check_items
        self.rand = round(time.time() * 1000)
        self.b64map = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"

        if use_hooks:
            setup_hooks(self.session)

    @staticmethod
    def int2char(a):
        return list("0123456789abcdefghijklmnopqrstuvwxyz")[a]

    def b64tohex(self, a):
        d = ""
        e = 0
        c = 0
        for i in range(len(a)):
            if list(a)[i] != "=":
                v = self.b64map.index(list(a)[i])
                if e == 0:
                    e = 1
                    d += self.int2char(v >> 2)
                    c = 3 & v
                elif e == 1:
                    e = 2
                    d += self.int2char(c << 2 | v >> 4)
                    c = 15 & v
                elif e == 2:
                    e = 3
                    d += self.int2char(c)
                    d += self.int2char(v >> 2)
                    c = 3 & v
                else:
                    e = 0
                    d += self.int2char(c << 2 | v >> 4)
                    d += self.int2char(15 & v)
        if e == 1:
            d += self.int2char(c << 2)
        return d

    def mask_phone(self, phone):
        return f'{phone[:3]}****{phone[-4:]}' if len(phone) == 11 else phone

    def rsa_encode(self, j_rsakey, string):
        rsa_key = f"-----BEGIN PUBLIC KEY-----\n{j_rsakey}\n-----END PUBLIC KEY-----"
        pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(rsa_key.encode())
        return self.b64tohex(
            (base64.b64encode(rsa.encrypt(f"{string}".encode(), pubkey))).decode()
        )

    def refresh_access_token(self, phonesrt):
        refresh_token = read(f'{phonesrt}.refreshToken') if phonesrt else ''
        if not refresh_token:
            return False

        try:
            self.session.headers.clear()
            response = self.session.post(
                "https://open.e.189.cn/api/oauth2/refreshToken.do",
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "application/json;charset=UTF-8",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "format": "json",
                    "clientId": "8025431004",
                    "grantType": "refresh_token",
                    "refreshToken": refresh_token
                }
            )

            if response.status_code == 200:
                res = response.json()
                if res.get('result') == 0:
                    write(phonesrt, res)
        except:
            return False
        return True

    def login(self, username, password):
        try:
            token_url = 'https://m.cloud.189.cn/udb/udb_login.jsp?pageId=1&pageKey=default&clientType=wap&' \
                        'redirectURL=https://m.cloud.189.cn/zhuanti/2021/shakeLottery/index.html'
            response = self.session.get(token_url)
            match = re.search(r"https?://[^\s'\"]+", response.text)
            if not match:
                print(" 错误：未找到动态登录页")
                return False

            url = match.group()
            response = self.session.get(url)
            match = re.search(r"<a id=\"j-tab-login-link\"[^>]*href=\"([^\"]+)\"", response.text)
            if not match:
                print(" 错误：登录入口获取失败")
                return False

            href = match.group(1)
            response = self.session.get(href)

            captcha_token = re.findall(r"captchaToken' value='(.+?)'", response.text)[0]
            lt = re.findall(r'lt = "(.+?)"', response.text)[0]
            return_url = re.findall(r"returnUrl= '(.+?)'", response.text)[0]
            param_id = re.findall(r'paramId = "(.+?)"', response.text)[0]
            j_rsakey = re.findall(r'j_rsaKey" value="(\S+)"', response.text, re.M)[0]
            self.session.headers.update({"lt": lt})

            username_encrypted = self.rsa_encode(j_rsakey, username)
            password_encrypted = self.rsa_encode(j_rsakey, password)

            # 准备登录数据
            data = {
                "appKey": "cloud",
                "accountType": '01',
                "userName": f"{{RSA}}{username_encrypted}",
                "password": f"{{RSA}}{password_encrypted}",
                "validateCode": "",
                "captchaToken": captcha_token,
                "returnUrl": return_url,
                "mailSuffix": "@189.cn",
                "paramId": param_id
            }

            headers = {
                'User-Agent': self.user_agent,
                'Referer': 'https://open.e.189.cn/',
            }

            # 提交登录请求
            response = self.session.post(
                "https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do",
                data=data, headers=headers, timeout=10
            )
            # 检查登录结果
            if response.json().get('result', 1) != 0:
                print(f" 登录错误：{response.json().get('msg')}")
                return False

            self.session.get(response.json()['toUrl'])
            print('用户名密码登录成功')
            return True

        except Exception as e:
            print(f" 登录异常：{str(e)}")
            return False

    def tokenlogin(self, phonesrt):
        accessToken = read(f'{phonesrt}.accessToken') if phonesrt else ''
        if not accessToken:
            return False
        token_sign_url = (
            'https://api.cloud.189.cn/getSessionForPC.action?'
            'appId=8025431004&clientType=TELEPC&ersion=9.0.6&'
            f'channelId=web_cloud.189.cn&rand={self.rand}&accessToken={accessToken}'
        )

        headers = {
            "User-Agent": self.user_agent,
            "accept-encoding": "gzip, deflate, br",
            "accept": "application/json;charset=UTF-8"
        }
        response = self.session.post(token_sign_url, headers=headers)
        if not response.status_code == 200:
            return False

        sessionKey = response.json().get('sessionKey')
        url = f'https://cloud.189.cn/api/portal/mkt/userSign.action?rand={self.rand}&clientType=TELEANDROID&version=9.0.6&model=KB2000&sessionKey={sessionKey}'

        self.session.headers.update({"referer": "https://cloud.189.cn/web/main/",})
        response = self.session.get(url)
        if response.status_code == 200:
            print('用token登录成功')
            return True
        return False

    def sign(self, phone, password, i):
        phonesrt = self.mask_phone(phone)
        msg = f"--- {phonesrt} 天翼云盘签到结果 ---\n{now()}\n"
        signKey = f"189_sign_{i}"
        if read(signKey) == today():
            return f"{msg}✅ 今日已签到"

        sign_in_result = "<b><span style='color: green'>签到成功</span></b>\n"

        if not (self.tokenlogin(phonesrt) or self.login(phone, password)):
            return f"{msg}<b><span style='color: red'>登录失败！</span></b>"

        try:
            self.session.headers.clear()
            self.session.headers.update({
                "Host": "m.cloud.189.cn",
                "Referer": "https://m.cloud.189.cn/zhuanti/2016/sign/index.jsp?albumBackupOpened=1",
                'User-Agent': 'iPhone;6.27.8;14.4;network/wifi;Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148;',
            })
            surl = (
                f"https://api.cloud.189.cn/mkt/userSign.action?"
                f"rand={self.rand}&clientType=TELEANDROID&version=10.3.11&model=24115RA8EC"
            )

            response = self.session.get(surl).json()
            netdiskbonus = response.get("netdiskBonus")
            if response.get("isSign") == False:
                iso_str = response.get("signTime")
                readable_str = datetime.fromisoformat(iso_str).astimezone().strftime("%Y-%m-%d %H:%M:%S")
                msg += f"获得 {netdiskbonus}M 空间\n签到时间：{readable_str}"
            else:
                write(signKey, today())
                msg += f"{sign_in_result}获得 {netdiskbonus}M 空间"

            url = (
                "https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?"
                "taskId=TASK_SIGNIN&activityId=ACT_SIGNIN"
            )
            response = self.session.get(url).json()
            if "errorCode" in response:
                msg +=  f"\n抽奖: 获得 {response.get('errorCode')}"
            else:
                prize = response.get('prizeName') or response.get('description', '未知奖品')
                msg +=  f"\n抽奖: 获得 {prize}"

            match = re.search(r'sessionKey=[^,]+', str(response))
            sessionKey = match.group(0) if match else ''

            if sessionKey:
                self.session.headers.clear()
                headers = {
                    "Host": "cloud.189.cn",
                    "User-Agent": self.user_agent,
                    "accept-encoding": "gzip, deflate, br",
                    "accept": "application/json;charset=UTF-8",
                    "referer": "https://cloud.189.cn/web/main/",
                }
                sizeinfourl = f"https://cloud.189.cn/api/portal/getUserSizeInfo.action?{sessionKey}"
                response = self.session.get(sizeinfourl, headers=headers, allow_redirects=False)
                try:
                    size_data = response.json()
                    if size_data.get("res_code") == 0:
                        def format_size(bytes):
                            if bytes >= 1024 **4:
                                return f"{bytes / (1024**4):.2f} TB"
                            elif bytes >= 1024** 3:
                                return f"{bytes / (1024 **3):.2f} GB"
                            else:
                                return f"{bytes / (1024** 2):.2f} MB"

                        total_size = size_data.get("totalSize", 0)
                        cloud_info = size_data.get("cloudCapacityInfo", {})
                        family_info = size_data.get("familyCapacityInfo", {})

                        size_lines =  [
                            f"\n\n总空间: {format_size(total_size)}",
                            "\n📦 个人容量",
                            f"\n  个人总容量: {format_size(cloud_info.get('totalSize', 0))}",
                            f"\n  个人已用: {format_size(cloud_info.get('usedSize', 0))}",
                            f"\n  个人剩余: {format_size(cloud_info.get('freeSize', 0))}",
                            "\n\n👨‍👩‍👧‍👦 家庭容量",
                            f"\n  家庭总容量: {format_size(family_info.get('totalSize', 0))}",
                            f"\n  家庭已用: {format_size(family_info.get('usedSize', 0))}",
                            f"\n  家庭剩余: {format_size(family_info.get('freeSize', 0))}"
                        ]

                        msg += ''.join(size_lines)
                except Exception as e:
                    msg += f"\n处理容量信息时出错: {str(e)}"

        except Exception as e:
            msg += f" 操作异常{str(e)}"
        finally:
            self.refresh_access_token(phonesrt)
            self.session.close()

        return msg

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            if i > 1:
                time.sleep(3)
            phone = check_item.get("phone")
            password = check_item.get("password")
            msg = self.sign(phone, password, i)
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    check_items = get_data().get("CLOUD189", [])
    result = Cloud189(check_items).main()
    if re.search(r'成功|失败|异常|错误|登录', result):
        send("天翼云盘 签到", result)
    else:
        print(result)
    # print(result)
