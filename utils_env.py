# -*- coding: utf-8 -*-
import os
import platform

ENV = ""  # 全局环境缓存

def get_env_str() -> str:
    """检测运行环境并返回环境标识字符串"""
    global ENV
    if ENV:
        return ENV
    
    # 定义环境检测规则（路径，环境名称）
    ENV_RULES = [
        (lambda: os.getenv("GITHUB_ACTIONS"), "github"),
        ("/usr/local/app/script/Lists/task.list", "v2p"),
        ("/ql/data/config/token.json", "ql_new"),
        ("/ql/config/env.sh", "ql")
    ]
    
    # print("正在检测运行环境...")
    for rule in ENV_RULES:
        if isinstance(rule[0], str):
            check = os.path.exists(rule[0])
        else:
            check = rule[0]()
        
        if check:
            # print(f"当前环境为: {rule[1]} 环境")
            ENV = rule[1]
            break
    else:  # 未匹配到任何面板环境时检测系统
        system = platform.system()
        if system in {"Windows", "Linux", "Darwin"}:
            # print(f"当前系统环境: {system}")
            ENV = system
        else:
            # print("环境检测失败")
            ENV = ""

    # print("环境检测完成\n")
    return ENV

def get_env_int() -> int:
    """返回环境对应的数字标识"""
    env_map = {
        "Windows": 0, "Linux": 1, "Darwin": 2,
        "github": 3, "v2p": 4, "ql_new": 5, "ql": 6
    }
    return env_map.get(get_env_str(), -1)

def get_file_path(file_name: str) -> str:
    """获取指定文件在对应环境中的路径"""
    env = get_env_str()
    # print(f"正在检查配置文件: {file_name}...")
    
    # 定义环境路径映射
    path_templates = {
        "v2p": "/usr/local/app/script/Lists/{}",
        "ql_new": "/ql/data/config/{}",
        "ql": "/ql/config/{}"
    }
    
    # 生成完整路径
    full_path = path_templates.get(env, "{}").format(file_name)
    
    if not os.path.exists(full_path):
        # print(f"配置文件未找到（可能正常）: {full_path}")
        return ""
    
    # print(f"已找到配置文件: {full_path}\n")
    return full_path
