# -*- coding: utf-8 -*-

import tomli
import traceback
import utils_env
import os, sys, json, time, re
from datetime import datetime, timedelta

DATA: dict = {}
_FILE = "magic.json"

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
    if not os.path.exists(_FILE):
        return {}
    try:
        with open(_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def read(key):
    return _load().get(key)

def write(key, val):
    data = _load()
    if val is None:
        data.pop(key, None)
    else:
        data[key] = val
    with open(_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def delete(key):
    write(key, None)

def today(tomorrow_if_late=False):
    now_time = datetime.now()
    if tomorrow_if_late and now_time.hour == 23 and 50 <= now_time.minute <= 59:
        tomorrow = now_time + timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d")
    return now_time.strftime("%Y-%m-%d")

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def sleep(m):
    time.sleep(m)

def wait_midnight(**kwargs):
    stime = kwargs.get('stime', 2)
    wait = kwargs.get('wait', True)
    offset = kwargs.get('offset', 0)
    retries = kwargs.get('retries', 15)
    base_url = kwargs.get('base_url', '')
    session = kwargs.get('session', None)

    now_time = datetime.now()
    if wait and now_time.hour == 23 and 56 <= now_time.minute <= 59:
        midnight = (now_time + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        sleep_seconds = int((midnight - now_time).total_seconds()) + offset
        hours, remainder = divmod(sleep_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"将在 {midnight.strftime('%H:%M:%S')} 执行，等待 {hours} 小时 {minutes} 分 {seconds} 秒")

        total_wait = sleep_seconds
        start_time = time.time()
        while sleep_seconds > 0:
            chunk = min(20, sleep_seconds)
            sleep(chunk)
            sleep_seconds -= chunk

            if sleep_seconds > 0:
                elapsed = time.time() - start_time
                percent = min(100, 100 * elapsed / total_wait)
                remaining_min, remaining_sec = divmod(sleep_seconds, 60)
                print(f"[{now()}] 剩余 {remaining_min:.0f}分 {remaining_sec:.0f}秒，进度 {percent:.1f}%")

    if session and base_url:
        for retry in range(retries):
            get_response = session.get(base_url)
            if not re.search(r'今天已经签过到了|已经签到|今日已签', get_response.text):
                break
            print(f'检测到已签到，等待{stime}秒后重试... ({retry+1}/{retries})')
            sleep(stime)
