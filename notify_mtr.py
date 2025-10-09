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
    'HITOKOTO': False,
    'BARK_PUSH': '', 'BARK_ARCHIVE': '', 'BARK_GROUP': '', 'BARK_SOUND': '', 'BARK_ICON': '',
    'CONSOLE': True,
    'DD_BOT_SECRET': '', 'DD_BOT_TOKEN': '',
    'DEER_KEY': '', 'FSKEY': '',
    'GOBOT_URL': '', 'GOBOT_QQ': '', 'GOBOT_TOKEN': '',
    'GOTIFY_URL': '', 'GOTIFY_TOKEN': '', 'GOTIFY_PRIORITY': 0,
    'IGOT_PUSH_KEY': '', 'PUSH_KEY': '',
    'PUSH_PLUS_TOKEN': '', 'PUSH_PLUS_USER': '',
    'QMSG_KEY': '', 'QMSG_TYPE': '',
    'QYWX_AM': '', 'QYWX_KEY': '',
    'TG_BOT_TOKEN': '', 'TG_USER_ID': '',
    'TG_API_HOST': '', 'TG_PROXY_AUTH': '', 'TG_PROXY_HOST': '', 'TG_PROXY_PORT': '',
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

# ========== 各通知服务 ==========
def bark(title, content):
    url_base = push_config['BARK_PUSH']
    if not url_base: return
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
    data = {"text": title, "desp": content, "type": "markdown", "pushkey": key}
    r = safe_request("POST", "https://api2.pushdeer.com/message/push", data=data)
    if r and r.json().get("content", {}).get("result"):
        print("✅ PushDeer 推送成功")

def feishu_bot(title, content):
    key = push_config["FSKEY"]
    if not key: return
    url = f"https://open.feishu.cn/open-apis/bot/v2/hook/{key}"
    data = {"msg_type": "text", "content": {"text": f"{title}\n\n{content}"}}
    r = safe_request("POST", url, data=json.dumps(data))
    if r and r.json().get("StatusCode") == 0:
        print("✅ 飞书 推送成功")

def gotify(title, content):
    if not (push_config["GOTIFY_URL"] and push_config["GOTIFY_TOKEN"]): return
    url = f"{push_config['GOTIFY_URL'].rstrip('/')}/message?token={push_config['GOTIFY_TOKEN']}"
    data = {"title": title, "message": content, "priority": push_config["GOTIFY_PRIORITY"]}
    r = safe_request("POST", url, data=data)
    if r and r.json().get("id"):
        print("✅ Gotify 推送成功")

def wecom_bot(title, content):
    key = push_config["QYWX_KEY"]
    if not key: return
    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}"
    data = {"msgtype": "text", "text": {"content": f"{title}\n\n{content}"}}
    r = safe_request("POST", url, data=json.dumps(data))
    if r and r.json().get("errcode") == 0:
        print("✅ 企业微信机器人 推送成功")

def telegram_bot(title, content):
    tok, uid = push_config["TG_BOT_TOKEN"], push_config["TG_USER_ID"]
    if not (tok and uid): return
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

def pushplus_bot(title, content):
    if not push_config["PUSH_PLUS_TOKEN"]: return
    url = "http://www.pushplus.plus/send"
    data = {
        "token": push_config["PUSH_PLUS_TOKEN"],
        "title": title,
        "content": content,
        "topic": push_config["PUSH_PLUS_USER"],
    }
    r = safe_request("POST", url, json=data)
    if r and r.json().get("code") == 200:
        print("✅ PushPlus 推送成功")

def serverJ(title, content):
    key = push_config["PUSH_KEY"]
    if not key: return
    if "SCT" in key:
        url = f"https://sctapi.ftqq.com/{key}.send"
    else:
        url = f"https://sc.ftqq.com/{key}.send"
    data = {"text": title, "desp": content.replace("\n", "\n\n")}
    r = safe_request("POST", url, data=data)
    if r and (r.json().get("code") == 0 or r.json().get("errno") == 0):
        print("✅ Server酱 推送成功")

# ========== 一言 ==========
def one():
    try:
        return requests.get("https://v1.hitokoto.cn/").json().get("hitokoto", "")
    except Exception:
        return ""

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

def send(title, content):
    if not content:
        print(f"⚠️ 内容为空，取消推送。")
        return
    if push_config["HITOKOTO"]:
        content += "\n\n> " + one()
    threads = [threading.Thread(target=f, args=(title, content), name=f.__name__) for f in notify_function]
    [t.start() for t in threads]
    [t.join() for t in threads]

# ========== 入口 ==========
def main():
    send("测试标题", "这是一条来自 NotifyPro 的测试消息")

if __name__ == "__main__":
    main()
