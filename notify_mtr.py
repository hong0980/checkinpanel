import base64, hashlib, hmac, json, os, re, threading, time, traceback, urllib.parse, requests, tomllib
from utils_env import get_file_path

# ========== 基础工具 ==========
_print = print
mutex = threading.Lock()
def print(*args, **kw):
    with mutex:
        _print(*args, **kw)

def safe_request(method: str, url: str, **kwargs):
    try:
        r = requests.request(method, url, timeout=15, **kwargs)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"❌ 网络请求失败：{url} -> {e}")
        return None

# ========== Markdown/HTML 转换 ==========
link_reg = re.compile(r"<a href=['|\"](.+?)['|\"]>(.+?)</a>")
bold_reg = re.compile(r"<b>(.+?)</b>")
list_reg = re.compile(r"^(\d+\.|-)\s.+$")
def html2md(content: str) -> str:
    content = "\n".join(
        map(lambda x: x if list_reg.fullmatch(x) else x + "\n", content.split("\n"))
    )
    return bold_reg.sub(r"### **\1**", link_reg.sub(r"[\2](\1)", content))

# ========== 加载配置 ==========
DEFAULT_CONFIG = {
    'HITOKOTO': True,                   # 启用一言（随机句子）
    'CONSOLE': False,                   # 控制台输出

    'BARK_PUSH': '',                    # bark IP 或设备码，例：https://api.day.app/DxHcxxxxxRxxxxxxcm/
    'BARK_ARCHIVE': '',                 # bark 推送是否存档
    'BARK_GROUP': '',                   # bark 推送分组
    'BARK_SOUND': '',                   # bark 推送声音
    'BARK_ICON': '',                    # bark 推送图标
    'BARK_LEVEL': '',                   # bark 推送时效性
    'BARK_URL': '',                     # bark 推送跳转URL

    'DD_BOT_SECRET': '',                # 钉钉机器人的 DD_BOT_SECRET
    'DD_BOT_TOKEN': '',                 # 钉钉机器人的 DD_BOT_TOKEN

    'FSKEY': '',                        # 飞书机器人的 FSKEY

    'GOBOT_URL': '',                    # go-cqhttp
                                        # 推送到个人QQ：http://127.0.0.1/send_private_msg
                                        # 群：http://127.0.0.1/send_group_msg
    'GOBOT_QQ': '',                     # go-cqhttp 的推送群或用户
                                        # GOBOT_URL 设置 /send_private_msg 时填入 user_id=个人QQ
                                        #               /send_group_msg   时填入 group_id=QQ群
    'GOBOT_TOKEN': '',                  # go-cqhttp 的 access_token

    'GOTIFY_URL': '',                   # gotify地址,如https://push.example.de:8080
    'GOTIFY_TOKEN': '',                 # gotify的消息应用token
    'GOTIFY_PRIORITY': 0,               # 推送消息优先级,默认为0

    'IGOT_PUSH_KEY': '',                # iGot 聚合推送的 IGOT_PUSH_KEY

    'PUSH_KEY': '',                     # server 酱的 PUSH_KEY，兼容旧版与 Turbo 版

    'DEER_KEY': '',                     # PushDeer 的 PUSHDEER_KEY
    'DEER_URL': '',                     # PushDeer 的 PUSHDEER_URL

    'CHAT_URL': '',                     # synology chat url
    'CHAT_TOKEN': '',                   # synology chat token

    'PUSH_PLUS_TOKEN': '',              # pushplus 推送的用户令牌
    'PUSH_PLUS_USER': '',               # pushplus 推送的群组编码
    'PUSH_PLUS_TEMPLATE': 'html',       # pushplus 发送模板，支持html,txt,json,markdown,cloudMonitor,jenkins,route,pay
    'PUSH_PLUS_CHANNEL': 'wechat',      # pushplus 发送渠道，支持wechat,webhook,cp,mail,sms
    'PUSH_PLUS_WEBHOOK': '',            # pushplus webhook编码，可在pushplus公众号上扩展配置出更多渠道
    'PUSH_PLUS_CALLBACKURL': '',        # pushplus 发送结果回调地址，会把推送最终结果通知到这个地址上
    'PUSH_PLUS_TO': '',                 # pushplus 好友令牌，微信公众号渠道填写好友令牌，企业微信渠道填写企业微信用户id

    'WE_PLUS_BOT_TOKEN': '',            # 微加机器人的用户令牌
    'WE_PLUS_BOT_RECEIVER': '',         # 微加机器人的消息接收者
    'WE_PLUS_BOT_VERSION': 'pro',          # 微加机器人的调用版本

    'QMSG_KEY': '',                     # qmsg 酱的 QMSG_KEY
    'QMSG_TYPE': '',                    # qmsg 酱的 QMSG_TYPE

    'QYWX_ORIGIN': '',                  # 企业微信代理地址
    'QYWX_AM': '',                      # 企业微信应用
    'QYWX_KEY': '',                     # 企业微信机器人

    'TG_BOT_TOKEN': '',                 # tg 机器人的 TG_BOT_TOKEN，例：1407203283:AAG9rt-6RDaaX0HBLZQq0laNOh898iFYaRQ
    'TG_USER_ID': '',                   # tg 机器人的 TG_USER_ID，例：1434078534
    'TG_API_HOST': '',                  # tg 代理 api
    'TG_PROXY_AUTH': '',                # tg 代理认证参数
    'TG_PROXY_HOST': '',                # tg 机器人的 TG_PROXY_HOST
    'TG_PROXY_PORT': '',                # tg 机器人的 TG_PROXY_PORT

    'AIBOTK_KEY': '',                   # 智能微秘书 个人中心的apikey 文档地址：http://wechat.aibotk.com/docs/about
    'AIBOTK_TYPE': '',                  # 智能微秘书 发送目标 room 或 contact
    'AIBOTK_NAME': '',                  # 智能微秘书  发送群名 或者好友昵称和type要对应好

    'SMTP_SERVER': '',                  # SMTP 发送邮件服务器，形如 smtp.exmail.qq.com:465
    'SMTP_SSL': 'false',                # SMTP 发送邮件服务器是否使用 SSL，填写 true 或 false
    'SMTP_EMAIL': '',                   # SMTP 收发件邮箱，通知将会由自己发给自己
    'SMTP_PASSWORD': '',                # SMTP 登录密码，也可能为特殊口令，视具体邮件服务商说明而定
    'SMTP_NAME': '',                    # SMTP 收发件人姓名，可随意填写

    'PUSHME_KEY': '',                   # PushMe 的 PUSHME_KEY
    'PUSHME_URL': '',                   # PushMe 的 PUSHME_URL

    'CHRONOCAT_QQ': '',                 # qq号
    'CHRONOCAT_TOKEN': '',              # CHRONOCAT 的token
    'CHRONOCAT_URL': '',                # CHRONOCAT的url地址

    'WEBHOOK_URL': '',                  # 自定义通知 请求地址
    'WEBHOOK_BODY': '',                 # 自定义通知 请求体
    'WEBHOOK_HEADERS': '',              # 自定义通知 请求头
    'WEBHOOK_METHOD': '',               # 自定义通知 请求方法
    'WEBHOOK_CONTENT_TYPE': '',         # 自定义通知 content-type

    'NTFY_URL': '',                     # ntfy地址,如https://ntfy.sh
    'NTFY_TOPIC': '',                   # ntfy的消息应用topic
    'NTFY_PRIORITY':'3',                # 推送消息优先级,默认为3
    'NTFY_TOKEN': '',                   # 推送token,可选
    'NTFY_USERNAME': '',                # 推送用户名称,可选
    'NTFY_PASSWORD': '',                # 推送用户密码,可选
    'NTFY_ACTIONS': '',                 # 推送用户动作,可选

    'WXPUSHER_APP_TOKEN': '',           # wxpusher 的 appToken 官方文档: https://wxpusher.zjiecode.com/docs/ 管理后台: https://wxpusher.zjiecode.com/admin/
    'WXPUSHER_TOPIC_IDS': '',           # wxpusher 的 主题ID，多个用英文分号;分隔 topic_ids 与 uids 至少配置一个才行
    'WXPUSHER_UIDS': '',                # wxpusher 的 用户ID，多个用英文分号;分隔 topic_ids 与 uids 至少配置一个才行
}
CONFIG_PATH = os.getenv("NOTIFY_CONFIG_PATH") or get_file_path("notify.toml")

def load_config():
    cfg = DEFAULT_CONFIG.copy()
    for k in cfg:
        if v := os.getenv(k):
            cfg[k] = v
    if os.path.exists(CONFIG_PATH):
        # print(f"✅ 读取通知配置文件：{CONFIG_PATH}")
        try:
            data = tomllib.load(open(CONFIG_PATH, "rb"))
            for k, v in data.items():
                if k in cfg:
                    cfg[k] = v
        except tomllib.TOMLDecodeError:
            print(f"⚠️ TOML 格式错误：{CONFIG_PATH}\n{traceback.format_exc()}")
    return cfg

push_config = load_config()

def bark(title, content):
    url_base = push_config['BARK_PUSH']
    if not url_base: return
    print("Bark 服务启动")
    if not url_base.startswith("http"):
        url_base = f"https://api.day.app/{url_base}"
    url = f"{url_base}/{urllib.parse.quote_plus(title)}/{urllib.parse.quote_plus(content)}"
    params = {k.lower(): v for k,v in {
        "BARK_ARCHIVE": push_config["BARK_ARCHIVE"],
        "BARK_GROUP": push_config["BARK_GROUP"],
        "BARK_SOUND": push_config["BARK_SOUND"],
        "BARK_ICON": push_config["BARK_ICON"],
    }.items() if v}
    r = safe_request("GET", url, params=params)
    if r and r.json().get("code") == 200:
        print("✅ Bark 推送成功")

def console(title, content):
    print(f"\n🖥️ [{title}]\n{content}\n")

def dingding_bot(title, content):
    sec, tok = push_config["DD_BOT_SECRET"], push_config["DD_BOT_TOKEN"]
    if not (sec and tok): return
    print("钉钉 服务启动")
    ts = str(round(time.time() * 1000))
    sign = urllib.parse.quote_plus(
        base64.b64encode(
            hmac.new(sec.encode(), f"{ts}\n{sec}".encode(), hashlib.sha256).digest()
        )
    )
    url = f"https://oapi.dingtalk.com/robot/send?access_token={tok}&timestamp={ts}&sign={sign}"
    data = {"msgtype": "markdown", "markdown": {"title": title, "text": html2md(content)}}
    r = safe_request("POST", url, json=data)
    if r and r.json().get("errcode") == 0:
        print("✅ 钉钉 推送成功")

def pushdeer(title, content):
    key = push_config["DEER_KEY"]
    if not key: return
    print("PushDeer 服务启动")
    data = {"text": title, "desp": content, "type": "markdown", "pushkey": key}
    r = safe_request("POST", "https://api2.pushdeer.com/message/push", data=data)
    if r and r.json().get("content", {}).get("result"):
        print("✅ PushDeer 推送成功")

def feishu_bot(title, content):
    key = push_config["FSKEY"]
    if not key: return
    print("飞书 服务启动")
    url = f"https://open.feishu.cn/open-apis/bot/v2/hook/{key}"
    data = {"msg_type": "text", "content": {"text": f"{title}\n\n{content}"}}
    r = safe_request("POST", url, data=json.dumps(data))
    if r and r.json().get("StatusCode") == 0:
        print("✅ 飞书 推送成功")

def gotify(title, content):
    if not (push_config["GOTIFY_URL"] and push_config["GOTIFY_TOKEN"]): return
    print("gotify 服务启动")
    url = f"{push_config['GOTIFY_URL'].rstrip('/')}/message?token={push_config['GOTIFY_TOKEN']}"
    data = {"title": title, "message": content, "priority": push_config["GOTIFY_PRIORITY"]}
    r = safe_request("POST", url, data=data)
    if r and r.json().get("id"):
        print("✅ Gotify 推送成功")

def wecom_bot(title, content):
    key = push_config["QYWX_KEY"]
    if not key: return
    print("企业微信机器人服务启动")
    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}"
    data = {"msgtype": "text", "text": {"content": f"{title}\n\n{content}"}}
    r = safe_request("POST", url, data=json.dumps(data))
    if r and r.json().get("errcode") == 0:
        print("✅ 企业微信机器人 推送成功")

def telegram_bot(title, content):
    tok, uid = push_config["TG_BOT_TOKEN"], push_config["TG_USER_ID"]
    if not (tok and uid): return
    print("Telegram 服务启动")
    base = push_config["TG_API_HOST"] or "api.telegram.org"
    url = f"https://{base}/bot{tok}/sendMessage"
    data = {
        "chat_id": str(uid),
        "text": f"<b><u>{title}</u></b>\n\n{content}",
        "disable_web_page_preview": True,
        "parse_mode": "HTML",
    }
    proxies = None
    if push_config["TG_PROXY_HOST"] and push_config["TG_PROXY_PORT"]:
        proxy = f"http://{push_config['TG_PROXY_HOST']}:{push_config['TG_PROXY_PORT']}"
        proxies = {"http": proxy, "https": proxy}
    r = safe_request("POST", url, data=data, proxies=proxies)
    if r and r.json().get("ok"):
        print("✅ Telegram 推送成功")

pushplus_lock = threading.Lock()
pushplus_last = 0
PUSH_INTERVAL = 5  # 推送间隔(秒)
def pushplus_bot(title, content):
    global pushplus_last
    with pushplus_lock:
        # 计算并等待必要的间隔时间
        if time.time() - pushplus_last < PUSH_INTERVAL:
            time.sleep(PUSH_INTERVAL - (time.time() - pushplus_last))
        pushplus_last = time.time()

        if not push_config["PUSH_PLUS_TOKEN"]: return
        print("PushPlus 服务启动")
        try:
            r = safe_request("POST", "http://www.pushplus.plus/send", json={
                "title": title, "content": content,
                "token": push_config["PUSH_PLUS_TOKEN"],
                "to": push_config["PUSH_PLUS_TO"],
                "topic": push_config["PUSH_PLUS_USER"],
                "channel": push_config["PUSH_PLUS_CHANNEL"],
                "webhook": push_config["PUSH_PLUS_WEBHOOK"],
                "template": push_config["PUSH_PLUS_TEMPLATE"],
                "callbackUrl": push_config["PUSH_PLUS_CALLBACKURL"],
            }).json()
            print("✅ 推送成功" if r["code"] == 200 else f"❌ 错误: {r['msg']}")
        except Exception as e:
            print(f"❌ 推送失败: {e}")

def weplus_bot(title: str, content: str) -> None:
    if not push_config["WE_PLUS_BOT_TOKEN"]: return
    print("微加机器人 服务启动")

    template = "txt"
    if len(content) > 800:
        template = "html"

    url = "https://www.weplusbot.com/send"
    data = {
        "title": title,
        "content": content,
        "template": template,
        "token": push_config["WE_PLUS_BOT_TOKEN"],
        "receiver": push_config["WE_PLUS_BOT_RECEIVER"],
        "version": push_config["WE_PLUS_BOT_VERSION"],
    }
    body = json.dumps(data).encode(encoding="utf-8")
    headers = {"Content-Type": "application/json"}
    response = safe_request("POST", url, data=body, headers=headers).json()

    if response["code"] == 200:
        print("微加机器人 推送成功！")
    else:
        print("微加机器人 推送失败！")

def serverJ(title, content):
    key = push_config["PUSH_KEY"]
    if not key: return
    print("serverJ 服务启动")
    if "SCT" in key:
        url = f"https://sctapi.ftqq.com/{key}.send"
    else:
        url = f"https://sc.ftqq.com/{key}.send"
    data = {"text": title, "desp": content.replace("\n", "\n\n")}
    r = safe_request("POST", url, data=data)
    if r and (r.json().get("code") == 0 or r.json().get("errno") == 0):
        print("✅ Server酱 推送成功")

def aibotk(title: str, content: str) -> None:
    """
    使用 智能微秘书 推送消息。
    """
    if (
        not push_config.get("AIBOTK_KEY")
        or not push_config.get("AIBOTK_TYPE")
        or not push_config.get("AIBOTK_NAME")
    ): return
    print("智能微秘书 服务启动")

    if push_config.get("AIBOTK_TYPE") == "room":
        url = "https://api-bot.aibotk.com/openapi/v1/chat/room"
        data = {
            "apiKey": push_config.get("AIBOTK_KEY"),
            "roomName": push_config.get("AIBOTK_NAME"),
            "message": {"type": 1, "content": f"【青龙快讯】\n\n{title}\n{content}"},
        }
    else:
        url = "https://api-bot.aibotk.com/openapi/v1/chat/contact"
        data = {
            "apiKey": push_config.get("AIBOTK_KEY"),
            "name": push_config.get("AIBOTK_NAME"),
            "message": {"type": 1, "content": f"【青龙快讯】\n\n{title}\n{content}"},
        }
    body = json.dumps(data).encode(encoding="utf-8")
    headers = {"Content-Type": "application/json"}
    r = safe_request("POST", url, data=body, headers=headers)
    if r and (r.json().get("code") == 0):
        print("✅ 智能微秘书 推送成功")

# ========== 一言 ==========
def one() -> str:
    res = safe_request('GET', "https://v1.hitokoto.cn/").json()
    return f'{res["hitokoto"]}   ----{res["from"]}'

# ========== 调度器 ==========
notify_function = []
if push_config["BARK_PUSH"]: notify_function.append(bark)
if push_config["CONSOLE"]: notify_function.append(console)
if push_config["DD_BOT_TOKEN"] and push_config["DD_BOT_SECRET"]: notify_function.append(dingding_bot)
if push_config["DEER_KEY"]: notify_function.append(pushdeer)
if push_config["FSKEY"]: notify_function.append(feishu_bot)
if push_config["GOTIFY_URL"] and push_config["GOTIFY_TOKEN"]: notify_function.append(gotify)
if push_config["QYWX_KEY"]: notify_function.append(wecom_bot)
if push_config["TG_BOT_TOKEN"] and push_config["TG_USER_ID"]: notify_function.append(telegram_bot)
if push_config["PUSH_PLUS_TOKEN"]: notify_function.append(pushplus_bot)
if push_config["PUSH_KEY"]: notify_function.append(serverJ)
if push_config["WE_PLUS_BOT_TOKEN"]: notify_function.append(weplus_bot)

def send(title, content):
    if not content:
        print(f"⚠️ 内容为空，取消推送。")
        return
    if push_config["HITOKOTO"]:
        content += "\n\n> " + one()
    threads = [threading.Thread(target=f, args=(title, content), name=f.__name__) for f in notify_function]
    [t.start() for t in threads]
    [t.join() for t in threads]

def main():
    send("测试标题", "这是一条来自 NotifyPro 的测试消息")

if __name__ == "__main__":
    main()
