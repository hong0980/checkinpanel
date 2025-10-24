# -*- coding: utf-8 -*-
"""
cron: 20 1 0,12 * * *
new Env('51黑电子论坛 签到');
"""
import re, requests
from notify_mtr import send
from utils import get_data, store

class hei:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        signKey = f"51hei_sign_{i}"
        if store.has_signed(signKey): return (f"账号 {i}: ✅ 今日已签到")

        session = requests.session()
        url = 'http://www.51hei.com/bbs/home.php?mod=spacecp&ac=credit&op=base'
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/102.0.0.0 Safari/537.36",
        }
        try:
            r = session.get(url, headers=headers, timeout=10)
            name = re.findall(r'访问我的空间">(.*?)</a>', r.text)
            name = name[0] if name else None
            if name is None:
                return (f"<b><span style='color: red'>签到失败</span></b>\n"
                        f"账号({i})无法登录！可能Cookie失效，请重新修改")

            pattern = r'<em>\s*(黑币|威望|积分|贡献):\s*</em>(\d+)'
            matches = re.findall(pattern, r.text)
            res = (f"--- {name} 51黑电子论坛 签到结果 ---\n"
                   f"<b><span style='color: green'>签到成功</span></b>\n"
                   f"<br><b>账户信息</b>\n")
            res += ''.join([f'{match[0]}: {match[1]}\n' for match in matches])
            if re.search(r'签到成功', res): store.mark_signed(signKey)
            return res

        except Exception as e:
            return f"发生异常: {e}"

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = str(check_item.get("cookie"))
            msg_all += f'{self.sign(cookie, i)}\n\n'
        return msg_all

if __name__ == "__main__":
    _check_items = get_data().get("51HEI", [])
    result = hei(check_items=_check_items).main()
    if re.search(r'成功|失败', result):
        send("51黑电子论坛 签到", result)
    else:
        print(result)
    # print(result)
