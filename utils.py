# -*- coding: utf-8 -*-

from itertools import count
from requests import Response
import tomli, traceback,utils_env
import os, sys, json, time, re, urllib.parse
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter

DATA: dict = {}
_FILE = "magic.json"

class HookedAdapter(HTTPAdapter):
    _counter = count(1)

    def send(self, request, **kwargs):
        # 给这次请求分配一个序号
        request._hook_id = next(HookedAdapter._counter)

        parsed_url = urllib.parse.urlparse(request.url)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        start = time.time()
        self._request_hook(request, query_params, request._hook_id)
        response = super().send(request, **kwargs)
        cost = time.time() - start

        self._response_hook(response, cost, request._hook_id)
        return response

    def _request_hook(self, request, query_params, req_id: int):
        flat_params = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
        print(f"\n🔗 ========== 请求 #{req_id} ==========")
        print(f"➡️ 发送请求: {request.method} {request.url}")
        print(f"📝 请求参数:\n{json.dumps(flat_params, indent=2, ensure_ascii=False)}")
        print(f"📦 请求头:\n{json.dumps(dict(request.headers), indent=2, ensure_ascii=False)}")

    def _response_hook(self, response: Response, cost: float, req_id: int):
        print(f"\n📥 ========== 响应 #{req_id} ==========")
        print(f"✅ 收到响应: {response.status_code} {response.url}")
        print(f"⏱️ 耗时: {cost:.2f}s")
        print(f"📦 响应头:\n{json.dumps(dict(response.headers), indent=2, ensure_ascii=False)}")

        try:
            data = response.json()
            content = json.dumps(data, indent=2, ensure_ascii=False)
        except Exception:
            content = response.text

        content = content.strip()
        if len(content) > 1500:
            content = content[:1500].strip() + "\n...(已截断)"

        print(f"📄 响应数据:\n{content}")

        if response.status_code >= 400:
            print(f"⚠️ 请求失败，状态码 {response.status_code}")

def setup_hooks(session):
    try:
        session.mount('http://', HookedAdapter())
        session.mount('https://', HookedAdapter())
        return True
    except Exception as e:
        print(f"设置钩子失败: {str(e)}")
        return False

def _fatal(msg: str) -> None:
    """统一错误处理"""
    print(msg)
    sys.exit(1)

def get_data() -> dict:
    """获取签到配置"""
    global DATA
    if DATA:
        return DATA

    # 获取配置文件路径
    if check_config := os.getenv("CHECK_CONFIG"): #获取环境变量 CHECK_CONFIG
        if not os.path.exists(check_config):
            _fatal(f"错误：环境变量指定的配置文件 {check_config} 不存在！")
    else:
        if not (check_config := utils_env.get_file_path("check.toml")):
            _fatal("错误：未找到配置文件，请创建或设置 CHECK_CONFIG")

    # 加载配置文件
    try:
        with open(check_config, "rb") as f:
            DATA = tomli.load(f)
    except tomli.TOMLDecodeError:
        _fatal(f"配置文件格式错误\n参考: https://toml.io/cn/v1.0.0\n{traceback.format_exc()}")

    return DATA

def _load():
    if os.path.exists(_FILE):
        try:
            with open(_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def _save(data):
    with open(_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _get_nested(data, keys, default=None):
    cur = data
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def _set_nested(data, keys, val):
    cur = data
    for k in keys[:-1]:
        cur = cur.setdefault(k, {})
    if val is None:
        cur.pop(keys[-1], None)
    else:
        cur[keys[-1]] = val

def read(key=None, default=None):
    data = _load()
    if not key:
        return data
    return _get_nested(data, key.split("."), default)

def write(key, val):
    data = _load()
    _set_nested(data, key.split("."), val)
    _save(data)

def delete(key):
    write(key, None)

def update(values: dict):
    data = _load()
    for k, v in values.items():
        _set_nested(data, k.split("."), v)
    _save(data)

def today(tomorrow_if_late=False, late_hour=23, late_minute=50):
    now_time = datetime.now()
    target_date = now_time

    if tomorrow_if_late:
        threshold = now_time.replace(hour=late_hour, minute=late_minute, second=0, microsecond=0)
        if now_time >= threshold:
            target_date = now_time + timedelta(days=1)

    return target_date.strftime("%Y-%m-%d")

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def sleep(m):
    time.sleep(m)

def wait_midnight(**kwargs):
    stime   = kwargs.get('stime', 2)
    wait    = kwargs.get('wait', True)
    offset  = kwargs.get('offset', 0)
    retries = kwargs.get('retries', 15)
    base_url = kwargs.get('base_url', '')
    session = kwargs.get('session', None)

    now_time = datetime.now()
    if wait and now_time.hour == 23 and now_time.minute >= 55:
        target_time = (now_time.replace(hour=0, minute=0, second=0, microsecond=0)
                       + timedelta(days=1, seconds=offset))
        sleep_seconds = (target_time - now_time).total_seconds()

        total_wait = sleep_seconds
        h, rem = divmod(int(sleep_seconds), 3600)
        m, s = divmod(rem, 60)
        print(f"将在 {target_time.strftime('%H:%M:%S')} 执行，等待 {h} 小时 {m} 分 {s} 秒")

        while True:
            sleep_seconds = (target_time - datetime.now()).total_seconds()
            if sleep_seconds <= 0:
                break

            chunk = min(20, sleep_seconds)
            sleep(chunk)

            sleep_seconds = (target_time - datetime.now()).total_seconds()
            if sleep_seconds > 0:
                percent = 100 * (1 - sleep_seconds / total_wait)
                rm_min, rm_sec = divmod(int(sleep_seconds), 60)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"剩余 {rm_min}分 {rm_sec}秒，进度 {percent:.1f}%")

    if session and base_url:
        for retry in range(retries):
            r = session.get(base_url)
            if not re.search(r'今天已经签过到了|已经签到|今日已签', r.text):
                break
            print(f'检测到已签到，等待{stime}秒后重试... ({retry+1}/{retries})')
            sleep(stime)

    return True
