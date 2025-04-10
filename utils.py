# -*- coding: utf-8 -*-
import os
import sys
import tomli
import traceback
import utils_env

DATA: dict = {}

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
