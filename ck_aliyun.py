"""
cron: 10 6,18 * * *
new Env('阿里云盘  签到');
"""

import time, re
from notify_mtr import send
from requests_html import HTMLSession
from utils import store, get_data, update_data, setup_hooks

cfg = get_data()

class ALiYun:
    def __init__(self, check_items, use_hooks=True):
        self.session = HTMLSession()
        self.check_items = check_items
        if use_hooks:
            setup_hooks(self.session)

    def get_access_token(self, token: str):
        url = 'https://auth.aliyundrive.com/v2/account/token'
        res = self.session.post(url, json={'grant_type': 'refresh_token', 'refresh_token': token}, timeout=5).json()
        access_token = res.get('access_token', '')
        if not access_token:
            return '', ''
        name = res.get('user_name') or res.get('nick_name') or 'Unknown'

        store.write('ALiYun', {
            name: {
                'user_id': res['user_id'],
                'refresh_token': res['refresh_token'],
                'access_token': access_token
            }
        })

        update_data("ALiYun", "name", name, {
            'user_id': res['user_id'],
            'refresh_token': res['refresh_token'],
            'access_token': access_token
        }, path=cfg.get("__path__"))

        return name, access_token

    def check_in(self, token: str):
        """签到"""
        url = 'https://member.aliyundrive.com/v1/activity/sign_in_list'
        headers = {'Authorization': f'Bearer {token}'}
        res = self.session.post(url, json={'isReward': False}, params={'_rx-s': 'mobile'}, headers=headers, timeout=5).json()
        if 'success' not in res:
            return False, -1, res.get('message', '未知错误')
        return res['success'], res['result']['signInCount'], '签到成功'

    def get_reward(self, token: str, day: int):
        """领取奖励"""
        url = 'https://member.aliyundrive.com/v1/activity/sign_in_reward'
        headers = {'Authorization': f'Bearer {token}'}
        res = self.session.post(url, json={'signInDay': day}, params={'_rx-s': 'mobile'}, headers=headers, timeout=5).json()
        if 'result' not in res:
            return False, res.get('message', '未知错误')
        return res['success'], res['result']['notice']

    def get_drive_capacity(self, token: str):
        """查询云盘容量"""
        def fmt(size):
            for unit in ['MB', 'GB', 'TB']:
                if size < 1024:
                    return f"{size:.2f} {unit}"
                size /= 1024
            return f"{size:.2f} PB"

        try:
            res = self.session.post(
                'https://api.aliyundrive.com/adrive/v1/user/driveCapacityDetails',
                headers={'Authorization': f'Bearer {token}'},
                json={}
            ).json()
            return (
                "\n=== 云盘容量 ===\n"
                f"总空间: {fmt(res['drive_total_size']/1024**2)}\n"
                f"已用空间: {fmt(res['drive_used_size']/1024**2)}\n"
                f"备份已用: {fmt(res['backup_drive_used_size']/1024**2)}\n"
                f"备份文件: {fmt(res['default_drive_used_size']/1024**2)}\n"
                f"其他文件: {fmt(res['resource_drive_used_size']/1024**2)}\n"
                f"相册已用: {fmt(res['album_drive_used_size']/1024**2)}"
            )
        except Exception as e:
            return f"获取容量失败: {e}"

    def _sign_once(self, name, refresh_token, access_token, signKey):
        """单账号签到逻辑"""
        ok, count, info = self.check_in(access_token) if access_token else (False, 0, "")
        if not ok:
            print(f"{name} access_token 失效，尝试刷新...")
            _, access_token = self.get_access_token(refresh_token)
            if not access_token:
                return f"{name} token 刷新失败，跳过。\n"
            ok, count, info = self.check_in(access_token)
        if not ok:
            return f"{name} 签到失败：{info}\n"

        store.mark_signed(signKey)
        msg = f"--- {name} 阿里云盘 签到结果 ---\n"
        msg += f"本月已签到 {count} 次\n"
        ok, info = self.get_reward(access_token, count)
        msg += f"{name} 领取{'成功' if ok else '失败'}：{info}\n"
        msg += self.get_drive_capacity(access_token) + "\n"
        return msg

    def SignIn(self):
        msg = ""
        items = (
            list(self.check_items.items())
            if isinstance(self.check_items, dict)
            else [(acc.get("name") or f"账号{i+1}", acc)
                  for i, acc in enumerate(self.check_items)]
        )

        for i, (name, acc) in enumerate(items, 1):
            signKey = f"aliyun_sign_{i}"

            if store.has_signed(signKey):
                msg += f"{name} ✅ 今日已签到\n"
                continue

            if i > 1:
                time.sleep(3)
            print(f"{name} 开始签到...")

            refresh = acc.get("refresh_token")
            if not refresh:
                msg += f"{name} ⚠️ 缺少 refresh_token，跳过。\n"
                continue

            try:
                msg += self._sign_once(name, refresh, acc.get("access_token", ""), signKey)
            except Exception as e:
                msg += f"⚠️ {name} 出现异常：{e}\n"

        return msg.strip()

if __name__ == '__main__':
    check_items = cfg.get("ALiYun", []) or store.read('ALiYun')
    # check_items = store.read('ALiYun') or get_data().get("ALiYun", [])
    result = ALiYun(check_items, use_hooks=False).SignIn()
    if re.search(r'成功|失败|异常|错误|登录', result):
        send("阿里云盘 签到", result)
    else:
        print(result)
    # print(result)
