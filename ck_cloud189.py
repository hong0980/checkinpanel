# -*- coding: utf-8 -*-
"""
cron: 10 0,13 * * *
new Env('天翼云盘');
"""

from notify_mtr import send
import re, time, rsa, hashlib
from datetime import datetime
from requests_html import HTMLSession
from utils import store, get_data, setup_hooks

class Cloud189:
    def __init__(self, check_items, use_hooks=False):
        self.appId = "8025431004"
        self.app_key = "600100422"
        self.session = HTMLSession()
        self.check_items = check_items
        self.rand = str(int(time.time() * 1000))
        self.headers = {
            "accept-encoding": "gzip, deflate, br",
            "accept": "application/json;charset=UTF-8",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
        }
        if use_hooks:
            setup_hooks(self.session)

    def show_contact(self, phone):
        return f"{phone[:3]}****{phone[-4:]}" if len(phone) == 11 else phone

    def rsa_encode(self, j_rsakey: str, plaintext: str) -> str:
        rsa_key = f"-----BEGIN PUBLIC KEY-----\n{j_rsakey}\n-----END PUBLIC KEY-----"
        pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(rsa_key.encode())
        encrypted = rsa.encrypt(plaintext.encode(), pubkey)
        return encrypted.hex()

    def refresh_access_token(self, refreshToken, phone_masked):
        try:
            headers = self.headers
            headers.update({"content-type": "application/x-www-form-urlencoded"})
            data = {
                "format": "json",
                "clientId": self.appId,
                "grantType": "refresh_token",
                "refreshToken": refreshToken,
            }
            url = "https://open.e.189.cn/api/oauth2/refreshToken.do"
            resp = self.session.post(url, headers=headers, data=data)
            if resp.status_code == 200:
                res = resp.json()
                accessToken = res.get("accessToken", '')
                refreshToken = res.get("refreshToken", '')
                if accessToken and refreshToken:
                    print(f"{phone_masked} 刷新token成功")
                    store.write('cloud189', {phone_masked: {"accessToken": accessToken, "refreshToken": refreshToken}})
                    return accessToken

            print(f"token: {resp.json().get('msg')}")
        except Exception as e:
            print(f"刷新token异常: {e}")
        return None

    def userlogin(self, username, password, phone_masked):
        try:
            headers = self.headers
            uurl = 'https://cloud.189.cn/api/portal/unifyLoginForPC.action?' \
                    f'appId={self.appId}&clientType=10020&timeStamp={self.rand}&' \
                    'returnURL=https://m.cloud.189.cn/zhuanti/2020/loginErrorPc/index.html'

            resp = self.session.get(uurl, headers=headers)
            lt = re.search(r'lt = "(.+?)"', resp.text).group(1)
            paramId = re.search(r'paramId = "(.+?)"', resp.text).group(1)
            return_url = re.search(r"returnUrl = '(.+?)'", resp.text).group(1)
            j_rsaKey = resp.html.find("input[id=j_rsaKey]", first=True).attrs.get("value")
            captchaToken = resp.html.find("input[name=captchaToken]", first=True).attrs.get("value")
            username_encrypted = self.rsa_encode(j_rsaKey, username)
            password_encrypted = self.rsa_encode(j_rsaKey, password)
            data = {
                "isOauth2": False,
                "clientType": "1",
                "paramId": paramId,
                "validateCode": "",
                "cb_SaveName": "3",
                "accountType": "02",
                "appKey": self.appId,
                "dynamicCheck": "FALSE",
                "returnUrl": return_url,
                "captchaToken": captchaToken,
                "userName": f"{{RSA}}{username_encrypted}",
                "password": f"{{RSA}}{password_encrypted}",
            }
            headers.update({
                "referer": "https://open.e.189.cn", "lt": lt,
                "content-type": "application/x-www-form-urlencoded",
            })
            login_url = "https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do"
            resp = self.session.post(login_url, headers=headers, data=data).json()

            data = {
                "version": "6.2",
                "rand": self.rand,
                "appId": self.appId,
                "clientType": "TELEPC",
                "channelId": "web_cloud.189.cn",
                "redirectURL": resp.get("toUrl")
            }
            surl = "https://api.cloud.189.cn/getSessionForPC.action"
            resp = self.session.post(surl, headers=headers, data=data).json()

            sessionKey = resp.get("sessionKey")
            refreshToken = resp.get("refreshToken")
            accessToken = resp.get("accessToken", '')
            if not (accessToken or sessionKey):
                print(f"{phone_masked} 用户名密码登录失败")
                return False

            store.write('cloud189', {phone_masked: {"accessToken": accessToken, "refreshToken": refreshToken}})
            url = f"https://cloud.189.cn/api/open/oauth2/getAccessTokenBySsKey.action?sessionKey={sessionKey}"
            self.session.headers.clear()
            headers = self.headers.copy()
            headers.update({
                "Sign-Type": "1",
                "Timestamp": self.rand,
                "AppKey": self.app_key,
                "accept": "application/json;charset=UTF-8",
                "referer": "https://cloud.189.cn/web/main/",
                "Signature": hashlib.md5((self.app_key + self.rand + sessionKey).encode("utf-8")).hexdigest()
            })
            resp = self.session.get(url, headers=headers)
            if resp.json().get("accessToken"):
                print(f"{phone_masked} 用户名密码登录成功")
                store.write('cloud189', {phone_masked: {"expiresIn": resp.json().get("expiresIn")}})
                return sessionKey
            return False

        except Exception as e:
            print(f"{phone_masked} 登录异常: {e}")
            return False

    def tokenlogin(self, phone_masked):
        try:
            accessToken = store.read(f"cloud189.{phone_masked}.accessToken", "")
            refreshToken = store.read(f"cloud189.{phone_masked}.refreshToken", "")
            if not any([accessToken, refreshToken]):
                return False

            if not accessToken and refreshToken:
                if not (accessToken := self.refresh_access_token(refreshToken, phone_masked)):
                    return None

            url = "https://api.cloud.189.cn/getSessionForPC.action"
            data = {
                'rand': self.rand,
                'version': '9.0.6',
                'appId': self.appId,
                'clientType': 'TELEPC',
                'accessToken': accessToken,
                'channelId': 'web_cloud.189.cn'
            }

            self.session.headers.clear()
            resp = self.session.post(url, headers=self.headers, data=data)

            if resp.status_code == 200:
                sessionKey = resp.json().get("sessionKey")
                print(f"{phone_masked} 用token登录成功")
                return sessionKey
            else:
                print(f"{phone_masked} token登录失败")
                return False

        except Exception as e:
            return f" 操作异常{str(e)}"

    def sign(self, phone, password, i):
        phone_masked = self.show_contact(phone)
        msg = f"--- {phone_masked} 天翼云盘签到结果 ---\n{store.now()}\n"
        signKey = f"cloud189_sign_{i}"
        if store.has_signed(signKey):
            return f"{msg}✅ 今日已签到"

        sessionKey = self.tokenlogin(phone_masked) or self.userlogin(phone, password, phone_masked)
        if not sessionKey:
            return f"{msg}<b><span style='color: red'>登录失败！</span></b>"

        sign_in_result = "<b><span style='color: green'>签到成功</span></b>\n"
        try:
            self.session.headers.clear()
            headers = self.headers
            url = 'https://cloud.189.cn/api/portal/mkt/userSign.action?' \
                  f'model=KB2000&rand={self.rand}&version=9.0.6&' \
                  f'sessionKey={sessionKey}&clientType=TELEANDROID'
            headers.update({"referer": "https://cloud.189.cn/web/main/"})

            response = self.session.get(url, headers=headers).json()
            netdiskbonus = response.get("netdiskBonus")
            if response.get("isSign") == False:
                iso_str = response.get("signTime")
                readable_str = datetime.fromisoformat(iso_str).astimezone().strftime("%Y-%m-%d %H:%M:%S")
                msg += f"获得 {netdiskbonus}M 空间\n签到时间：{readable_str}"
            else:
                store.mark_signed(signKey)
                msg += f"{sign_in_result}获得 {netdiskbonus}M 空间"

            url = 'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN&activityId=ACT_SIGNIN'
            response = self.session.get(url).json()
            if "errorCode" in response:
                msg +=  f"\n抽奖: 获得 {response.get('errorCode')}"
            else:
                prize = response.get('prizeName') or response.get('description', '未知奖品')
                msg +=  f"\n抽奖: 获得 {prize}"

            try:
                url = f"https://cloud.189.cn/api/portal/getUserSizeInfo.action?sessionKey={sessionKey}"
                size_data = self.session.get(url, headers=headers).json()
                total_size = size_data.get("totalSize", 0)
                cloud_info = size_data.get("cloudCapacityInfo", {})
                family_info = size_data.get("familyCapacityInfo", {})
                def fm_size(size, precision=2):
                    try:
                        size = float(size)
                    except (TypeError, ValueError):
                        return "0 B"

                    if size < 0:
                        return "0 B"

                    units = ["B", "KB", "MB", "GB", "TB"]
                    for unit in units:
                        if size < 1024 or unit == "TB":
                            text = f"{size:.{precision}f}".rstrip("0").rstrip(".")
                            return f"{text} {unit}"
                        size /= 1024

                size_lines =  [
                    f"\n\n总空间: {fm_size(total_size)}",
                    "\n📦 个人容量",
                    f"\n  个人总容量: {fm_size(cloud_info.get('totalSize', 0))}",
                    f"\n  个人已用: {fm_size(cloud_info.get('usedSize', 0))}",
                    f"\n  个人剩余: {fm_size(cloud_info.get('freeSize', 0))}",
                    "\n\n👨‍👩‍👧‍👦 家庭容量",
                    f"\n  家庭总容量: {fm_size(family_info.get('totalSize', 0))}",
                    f"\n  家庭已用: {fm_size(family_info.get('usedSize', 0))}",
                    f"\n  家庭剩余: {fm_size(family_info.get('freeSize', 0))}"
                ]
                msg += ''.join(size_lines)

            except Exception as e:
                msg += f"\n处理容量信息时出错: {str(e)}"

        except Exception as e:
            msg += f" 操作异常{str(e)}"
        finally:
            self.session.close()
        return msg

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            if i > 1:
                time.sleep(3)
            phone = check_item.get("phone")
            password = check_item.get("password")
            if (phone and len(phone) == 11) and password:
                msg = self.sign(phone, password, i)
            else:
                msg = f"账号 {i} 用户名或密码错误"
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    check_items = get_data().get("CLOUD189", [])
    result = Cloud189(check_items).main()
    if re.search(r'成功|失败|异常|错误|登录|获得', result):
        send("天翼云盘 签到", result)
    else:
        print(result)
    # print(result)
