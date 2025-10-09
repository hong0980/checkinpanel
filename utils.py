# -*- coding: utf-8 -*-
from itertools import count
from requests import Response
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
import os, sys, json, time, re, urllib.parse, utils_env, tomllib, tomlkit

DATA = {}
DATA_PATH = ""
_FILE = "magic.json"

def _fatal(msg: str) -> None:
    """统一错误处理"""
    print(msg)
    sys.exit(1)

def get_data() -> dict:
    """获取全局 TOML 配置（带缓存）"""
    global DATA, DATA_PATH
    if DATA:
        return DATA

    # 获取配置文件路径
    if check_config := os.getenv("CHECK_CONFIG"):
        if not os.path.exists(check_config):
            _fatal(f"错误：环境变量指定的配置文件 {check_config} 不存在！")
    else:
        if not (check_config := utils_env.get_file_path("check.toml")):
            _fatal("错误：未找到配置文件，请创建或设置 CHECK_CONFIG")

    DATA_PATH = check_config
    with open(check_config, "rb") as f:
        DATA = tomllib.load(f)
    DATA["__path__"] = check_config
    return DATA

def update_data(table_name: str, match_field: str, match_value: str, updates: dict, path: str):
    with open(path, "r", encoding="utf-8") as f:
        doc = tomlkit.parse(f.read())

    if table_name not in doc:
        _fatal(f"配置文件中未找到 [[{table_name}]]")

    updated = False
    for item in doc[table_name]:
        if item.get(match_field) == match_value:
            item.update(updates)
            updated = True
            break

    if not updated:
        new_item = tomlkit.table()
        new_item.update({match_field: match_value, **updates})
        doc[table_name].append(new_item)

    with open(path, "w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(doc))

class HookedAdapter(HTTPAdapter):
    _counter = count(1)

    def send(self, request, **kwargs):
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
        if flat_params:
            print(f"📝 请求参数:\n{json.dumps(flat_params, indent=2, ensure_ascii=False)}")
        print(f"📦 请求头:\n{json.dumps(dict(request.headers), indent=2, ensure_ascii=False)}")

        body = request.body
        content_type = request.headers.get("Content-Type", "").lower()
        if not body:
            return

        content = None
        try:
            if "application/json" in content_type:
                if isinstance(body, (bytes, bytearray)):
                    body = body.decode("utf-8", errors="replace")
                parsed_body = json.loads(body)
                content = json.dumps(parsed_body, indent=2, ensure_ascii=False)

            elif "application/x-www-form-urlencoded" in content_type:
                if isinstance(body, (bytes, bytearray)):
                    body = body.decode("utf-8", errors="replace")
                parsed_qs = urllib.parse.parse_qs(body)
                flat_form = {k: v[0] if len(v) == 1 else v for k, v in parsed_qs.items()}
                content = json.dumps(flat_form, indent=2, ensure_ascii=False)

            elif "multipart/form-data" in content_type:
                content = "<multipart/form-data> 文件上传内容已省略"

            elif "text/" in content_type or "xml" in content_type:
                if isinstance(body, bytes):
                    body = body.decode("utf-8", errors="replace")
                content = body

            else:
                content = f"<{len(body)} bytes>" if isinstance(body, bytes) else str(body)

        except Exception as e:
            content = f"<无法解析请求体: {e}>"

        if content:
            content = content.strip()
            if len(content) > 1000:
                content = content[:1000] + "\n...(已截断)"
            print(f"📨 请求体:\n{content}")

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
        session.mount("http://", HookedAdapter())
        session.mount("https://", HookedAdapter())
        return True
    except Exception as e:
        print(f"设置钩子失败: {e}")
        return False

class Store:
    def __init__(self, path=_FILE):
        self.path = path

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save(self, data):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _get_nested(self, data, keys, default=None):
        cur = data
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur

    def _deep_update(self, d, u):
        for k, v in u.items():
            if isinstance(v, dict) and isinstance(d.get(k), dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v
        return d

    def read(self, key=None, default=None):
        data = self._load()
        if not key:
            return data
        return self._get_nested(data, key.split("."), default)

    def write(self, key, val):
        data = self._load()
        keys = key.split(".")
        cur = data
        for k in keys[:-1]:
            cur = cur.setdefault(k, {})

        last = keys[-1]
        if isinstance(cur.get(last), dict) and isinstance(val, dict):
            self._deep_update(cur[last], val)
        else:
            cur[last] = val
        self._save(data)

    def delete(self, key):
        data = self._load()
        keys = key.split(".")
        cur = data
        for k in keys[:-1]:
            cur = cur.get(k, {})
        cur.pop(keys[-1], None)
        self._save(data)

    def update(self, values: dict):
        data = self._load()
        for k, v in values.items():
            keys = k.split(".")
            cur = data
            for key in keys[:-1]:
                cur = cur.setdefault(key, {})
            cur[keys[-1]] = v
        self._save(data)

    # ======= 时间工具 =======
    @staticmethod
    def today(tomorrow_if_late=False, late_hour=23, late_minute=50):
        now_time = datetime.now()
        target_date = now_time
        if tomorrow_if_late:
            threshold = now_time.replace(hour=late_hour, minute=late_minute, second=0, microsecond=0)
            if now_time >= threshold:
                target_date += timedelta(days=1)
        return target_date.strftime("%Y-%m-%d")

    @staticmethod
    def now():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def sleep(seconds):
        time.sleep(seconds)


# 全局单例
store = Store()

def wait_midnight(**kwargs):
    stime   = kwargs.get('stime', 2)
    wait    = kwargs.get('wait', True)
    offset  = kwargs.get('offset', 0)
    retries = kwargs.get('retries', 20)
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
            store.sleep(chunk)

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
            store.sleep(stime)

    return True
