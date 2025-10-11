from itertools import count
from requests import Response
from tomlkit.items import AoT
from contextlib import contextmanager
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
import os, sys, json, time, re, urllib.parse, tomllib, tomlkit, fcntl

DATA = {}
DATA_PATH = ""
_FILE = "magic.json"

@contextmanager
def file_lock(path, mode="r+", lock_type="exclusive", encoding="utf-8", timeout=5, check_interval=0.05):
    lock_flag = fcntl.LOCK_EX if lock_type == "exclusive" else fcntl.LOCK_SH
    f = open(path, mode, encoding=encoding)

    start_time = time.time()
    while True:
        try:
            fcntl.flock(f, lock_flag | fcntl.LOCK_NB)
            break  # 成功锁定
        except BlockingIOError:
            if (time.time() - start_time) >= timeout:
                f.close()
                raise TimeoutError(f"获取文件锁超时: {path}")
            time.sleep(check_interval)

    try:
        yield f
    finally:
        try:
            f.flush()
            os.fsync(f.fileno())
        except Exception:
            pass
        fcntl.flock(f, fcntl.LOCK_UN)
        f.close()

def _fatal(msg: str) -> None:
    print(msg)
    sys.exit(1)

def get_data() -> dict:
    global DATA, DATA_PATH
    if DATA:
        return DATA

    if check_config := os.getenv("CHECK_CONFIG"):
        if not os.path.exists(check_config):
            _fatal(f"错误：环境变量指定的配置文件 {check_config} 不存在！")
    else:
        import utils_env
        if not (check_config := utils_env.get_file_path("check.toml")):
            _fatal("错误：未找到配置文件，请创建或设置 CHECK_CONFIG")

    DATA_PATH = check_config
    with open(check_config, "rb") as f:
        DATA = tomllib.load(f)
    DATA["__path__"] = check_config
    return DATA

def update_data(table_name: str, match_field: str, match_value: str, updates: dict, path: str):
    def make_item():
        t = tomlkit.table()
        t.update({match_field: match_value, **updates})
        return t

    with file_lock(path, "r+", "exclusive", timeout=5) as f:
        content = f.read().strip()
        doc = tomlkit.parse(content or "")
        table = doc.get(table_name)

        if table is None:
            aot = tomlkit.aot()
            aot.append(make_item())
            doc.add(table_name, aot)

        elif isinstance(table, AoT):
            updated = False
            empty_item = None
            for item in table:
                val = str(item.get(match_field, "")).strip().lower()
                if not val and empty_item is None:
                    empty_item = item
                if val == str(match_value).strip().lower():
                    item.update(updates)
                    updated = True
                    break
            if not updated:
                if empty_item is not None:
                    empty_item.update({match_field: match_value, **updates})
                else:
                    table.append(make_item())
        else:
            aot = tomlkit.aot()
            aot.append(table)
            aot.append(make_item())
            doc[table_name] = aot

        f.seek(0)
        f.truncate()
        f.write(tomlkit.dumps(doc).strip() + "\n")

class Store:
    def __init__(self, path=_FILE):
        self.path = path

    def _load(self):
        if not os.path.exists(self.path):
            return {}
        try:
            with file_lock(self.path, "r", "shared", timeout=3) as f:
                try:
                    return json.load(f)
                except Exception:
                    return {}
        except Exception as e:
            print(f"[store._load] 读取失败: {e}")
            return {}

    def _save(self, data):
        try:
            with file_lock(self.path, "w", "exclusive", timeout=5) as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except TimeoutError as e:
            print(f"[store._save] 超时未能写入: {e}")
            return False
        except Exception as e:
            print(f"[store._save] 写入失败: {e}")
            return False

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
        try:
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

            return self._save(data)
        except Exception as e:
            print(f"[store.write] 写入失败: {e}")
            return False

    def delete(self, key):
        data = self._load()
        keys = key.split(".")
        cur = data
        for k in keys[:-1]:
            cur = cur.get(k, {})
        cur.pop(keys[-1], None)
        return self._save(data)

    def update(self, values: dict):
        data = self._load()
        for k, v in values.items():
            keys = k.split(".")
            cur = data
            for key in keys[:-1]:
                cur = cur.setdefault(key, {})
            cur[keys[-1]] = v
        return self._save(data)

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

store = Store()

class HookedAdapter(HTTPAdapter):
    _counter = count(1)

    def __init__(self, truncate=True, max_req=1000, max_resp=1500):
        super().__init__()
        self.truncate = truncate
        self.max_req = max_req
        self.max_resp = max_resp

    def send(self, request, **kwargs):
        req_id = next(self._counter)
        start = time.time()

        self._print_request(request, req_id)
        response = super().send(request, **kwargs)
        self._print_response(response, req_id, time.time() - start)

        return response

    def _cut(self, text, limit):
        """简洁截断函数"""
        if not self.truncate or len(text) <= limit:
            return text
        return text[:limit] + "\n...(已截断)"

    def _print_request(self, req, req_id):
        url = req.url
        parsed = urllib.parse.urlparse(url)
        params = {k: v[0] if len(v) == 1 else v for k, v in urllib.parse.parse_qs(parsed.query).items()}

        print(f"\n🔗 ========== 请求 #{req_id} ==========")
        print(f"➡️ {req.method} {url}")
        if params: print(f"📝 参数:\n{json.dumps(params, indent=2, ensure_ascii=False)}")
        print(f"📦 请求头:\n{json.dumps(dict(req.headers), indent=2, ensure_ascii=False)}")

        body, ctype = req.body, req.headers.get("Content-Type", "").lower()
        if not body: return

        try:
            if isinstance(body, (bytes, bytearray)): body = body.decode("utf-8", "replace")
            if "json" in ctype:
                body = json.dumps(json.loads(body), indent=2, ensure_ascii=False)
            elif "x-www-form-urlencoded" in ctype:
                body = json.dumps({k: v[0] if len(v) == 1 else v for k, v in urllib.parse.parse_qs(body).items()}, indent=2, ensure_ascii=False)
            elif "multipart/form-data" in ctype:
                body = "<multipart/form-data> 文件上传内容已省略"
        except Exception as e:
            body = f"<无法解析请求体: {e}>"

        print(f"📨 请求体:\n{self._cut(body.strip(), self.max_req)}")

    def _print_response(self, resp: Response, req_id, cost):
        print(f"\n📥 ========== 响应 #{req_id} ==========")
        print(f"✅ {resp.status_code} {resp.url} ({cost:.2f}s)")
        print(f"📦 响应头:\n{json.dumps(dict(resp.headers), indent=2, ensure_ascii=False)}")

        try:
            text = json.dumps(resp.json(), indent=2, ensure_ascii=False)
        except Exception:
            text = resp.text or "<空响应>"

        print(f"📄 响应数据:\n{self._cut(text.strip(), self.max_resp)}")
        if resp.status_code >= 400:
            print(f"⚠️ 请求失败，状态码 {resp.status_code}")

def setup_hooks(session, truncate=True):
    """
    truncate: 是否截断长日志（默认读取环境变量 HOOK_TRUNCATE）
              - True / 1 / yes 启用截断
              - False / 0 / no  禁用截断
    """
    try:
        env_val = os.getenv("HOOK_TRUNCATE", "1").lower()
        if truncate is None:
            truncate = env_val in ("1", "true", "yes", "on")

        adapter = HookedAdapter(truncate=truncate)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return True
    except Exception as e:
        print(f"设置钩子失败: {e}")
        return False

def wait_midnight(**kwargs):
    stime    = kwargs.get('stime', 2)
    offset   = kwargs.get('offset', 0)
    wait     = kwargs.get('wait', True)
    retries  = kwargs.get('retries', 20)
    base_url = kwargs.get('base_url', '')
    session  = kwargs.get('session', None)

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

    r = None
    if session and base_url:
        for retry in range(retries):
            r = session.get(base_url)
            if not re.search(r'今天已经签过到了|已经签到|今日已签', r.text):
                break
            print(f'检测到已签到，等待{stime}秒后重试... ({retry+1}/{retries})')
            store.sleep(stime)

    return r
