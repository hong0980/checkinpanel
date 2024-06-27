# -*- coding: utf-8 -*-
"""
cron: 51 7 * * *
new Env('什么值得买');
"""

# 导入必要的库
from urllib.parse import quote, unquote  # 导入 urllib 库中的 quote 和 unquote 方法
import requests  # 导入 requests 库
from notify_mtr import send  # 从 notify_mtr 模块中导入 send 方法
from utils import get_data  # 从 utils 模块中导入 get_data 方法

# 定义一个名为 Smzdm 的类
class Smzdm:
    def __init__(self, check_items):
        self.check_items = check_items

    # 签到方法，传入 session 对象
    @staticmethod
    def sign(session):
        try:
            # 获取当前用户信息
            current = session.get(url="https://zhiyou.smzdm.com/user/info/jsonp_get_current").json()
            if current["checkin"]["has_checkin"]:
                # 用户已签到，获取用户信息并拼接消息
                msg = (
                    f"用户信息: {current.get('nickname', '')}\n"
                    f"目前积分: {current.get('point', '')}\n"
                    f"经验值: {current.get('exp', '')}\n"
                    f"金币: {current.get('gold', '')}\n"
                    f"碎银子: {current.get('silver', '')}\n"
                    f"威望: {current.get('prestige', '')}\n"
                    f"等级: {current.get('level', '')}\n"
                    f"已经签到: {current.get('checkin', {}).get('daily_checkin_num', '')} 天"
                )
            else:
                # 用户未签到，进行签到操作并获取签到数据，拼接消息
                data = session.get(url="https://zhiyou.smzdm.com/user/checkin/jsonp_checkin").json().get("data", {})
                msg = (
                    f"用户信息: {current.get('nickname', '')}\n"
                    f"目前积分: {data.get('point', '')}\n"
                    f"增加积分: {data.get('add_point', '')}\n"
                    f"经验值: {data.get('exp', '')}\n"
                    f"金币: {data.get('gold', '')}\n"
                    f"威望: {data.get('prestige', '')}\n"
                    f"等级: {data.get('rank', '')}\n"
                    f"已经签到: {data.get('checkin_num', {})} 天"
                )
        except Exception as e:
            # 签到失败，返回错误信息
            msg = f"签到状态: 签到失败\n错误信息: {e}，请重新获取 cookie"
        return msg

    # 主函数
    def main(self):
        msg_all = ""

        for check_item in self.check_items:
            # 遍历配置中的每个账号
            cookie = {
                item.split("=")[0]: quote(unquote(item.split("=")[1]))
                for item in check_item.get("cookie").split("; ")
                if item.split("=")[0] == "sess"
            }
            # 解析 cookie
            session = requests.session()  # 创建一个会话对象
            session.cookies.update(cookie)  # 更新会话对象的 Cookie
            session.headers.update(
                {
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                    "Connection": "keep-alive",
                    "Host": "zhiyou.smzdm.com",
                    "Referer": "https://www.smzdm.com/",
                    "Sec-Fetch-Dest": "script",
                    "Sec-Fetch-Mode": "no-cors",
                    "Sec-Fetch-Site": "same-site",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36",
                }
            )
            msg = self.sign(session)  # 调用签到方法
            msg_all += msg + "\n\n"
        return msg_all

# 如果是直接运行该脚本，则执行以下内容
if __name__ == "__main__":
    _data = get_data()  # 获取配置数据
    _check_items = _data.get("SMZDM", [])  # 获取“什么值得买”网站的配置信息
    result = Smzdm(check_items=_check_items).main()  # 执行签到操作
    send("什么值得买", result)  # 发送通知
    # print(result)
