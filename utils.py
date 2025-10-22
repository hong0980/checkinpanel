from itertools import count
from ruamel.yaml import YAML
from requests import Response
from tomlkit.items import AoT
from filelock import FileLock
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
import os, sys, json, time, re, urllib.parse, tomllib, tomlkit
from ruamel.yaml.comments import CommentedMap, CommentedSeq

DATA = {}
DATA_PATH = ""

def _fatal(msg: str):
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

    content = open(path, "r", encoding="utf-8").read() if os.path.exists(path) else ""
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
                empty_item.update(make_item())
            else:
                table.append(make_item())

    else:
        aot = tomlkit.aot()
        aot.append(table)
        aot.append(make_item())
        doc[table_name] = aot

    with open(path, "w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(doc).strip() + "\n")

class Store:
    def __init__(self, path="config.json"):
        self.path = path
        self.is_yaml = False
        self.lock = FileLock(f"{path}.lock")
        self.ext = os.path.splitext(path)[1].lower()

        if self.ext in [".yaml", ".yml"]:
            self.is_yaml = True
            self.yaml = YAML()
            self.yaml.preserve_quotes = True
            self.yaml.indent(mapping=2, sequence=4, offset=2)

    def _load(self):
        if not os.path.exists(self.path):
            return CommentedMap() if self.is_yaml else {}

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                if self.is_yaml:
                    data = self.yaml.load(f) or CommentedMap()
                    if not isinstance(data, (dict, CommentedMap)):
                        raise ValueError("YAML 根元素必须是映射类型")
                else:
                    data = json.load(f)
                return data
        except Exception as e:
            print(f"[ConfigStore._load] 读取失败: {e}")
            return CommentedMap() if self.is_yaml else {}

    def _save(self, data):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                if self.is_yaml:
                    self.yaml.dump(data, f)
                else:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[ConfigStore._save] 写入失败: {e}")
            return False

    def _deep_update(self, d, u):
        for k, v in u.items():
            if isinstance(v, dict) and isinstance(d.get(k), dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v
        return d

    def _get_nested(self, data, keys, default=None):
        cur = data
        for k in keys:
            if isinstance(cur, (list, CommentedSeq)) and k.isdigit():
                idx = int(k)
                if idx < len(cur):
                    cur = cur[idx]
                else:
                    return default
            elif isinstance(cur, (dict, CommentedMap)):
                cur = cur.get(k)
            else:
                return default
        return cur

    def read(self, key=None, default=None):
        with self.lock:
            data = self._load()
        if not key:
            return data
        return self._get_nested(data, key.split("."), default)

    def write(self, key, val, retry=5, retry_interval=0.1):
        for _ in range(retry):
            try:
                with self.lock:
                    data = self._load()
                    keys = key.split(".")
                    cur = data

                    for k in keys[:-1]:
                        if k.isdigit() and isinstance(cur, (list, CommentedSeq)):
                            k = int(k)
                            while len(cur) <= k:
                                cur.append(CommentedMap() if self.is_yaml else {})
                            cur = cur[k]
                        else:
                            cur = cur.setdefault(k, CommentedMap() if self.is_yaml else {})

                    last = keys[-1]
                    if isinstance(cur.get(last), dict) and isinstance(val, dict):
                        self._deep_update(cur[last], val)
                    else:
                        cur[last] = val

                    return self._save(data)
            except Exception as e:
                print(f"[ConfigStore.write] 写入失败: {e}")
                time.sleep(retry_interval)
        return False

    def delete(self, key):
        with self.lock:
            data = self._load()
            keys = key.split(".")
            cur = data
            for k in keys[:-1]:
                if isinstance(cur, (dict, CommentedMap)):
                    cur = cur.get(k, {})
                elif isinstance(cur, (list, CommentedSeq)) and k.isdigit():
                    idx = int(k)
                    cur = cur[idx] if idx < len(cur) else {}
                else:
                    return False
            last = keys[-1]
            if isinstance(cur, (dict, CommentedMap)):
                cur.pop(last, None)
            elif isinstance(cur, (list, CommentedSeq)) and last.isdigit():
                idx = int(last)
                if idx < len(cur):
                    cur.pop(idx)
            return self._save(data)

    def update(self, values: dict):
        with self.lock:
            data = self._load()
            for k, v in values.items():
                keys = k.split(".")
                cur = data
                for kk in keys[:-1]:
                    cur = cur.setdefault(kk, CommentedMap() if self.is_yaml else {})
                last = keys[-1]
                if isinstance(cur.get(last), dict) and isinstance(v, dict):
                    self._deep_update(cur[last], v)
                else:
                    cur[last] = v
            return self._save(data)

    @staticmethod
    def today(tomorrow_if_late=False):
        now = datetime.now()
        if tomorrow_if_late and now.hour >= 23 and now.minute >= 50:
            now += timedelta(days=1)
        return now.strftime("%Y-%m-%d")

    @staticmethod
    def now():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def sleep(seconds):
        time.sleep(seconds)

    def has_signed(self, key, tomorrow_if_late=False):
        return self.read(key) == self.today(tomorrow_if_late)

    def mark_signed(self, key):
        return self.write(key, self.today())

store = Store("magic.json")

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
            if not re.search(r'今天已经签过到了|已经签到|今日已签|已签', r.text):
                break
            print(f'检测到已签到，等待{stime}秒后重试... ({retry+1}/{retries})')
            store.sleep(stime)

    return r
