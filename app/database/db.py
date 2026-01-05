"""
JSON 配置文件读写模块
"""
import json
import os
from flask import current_app

# 全局配置缓存
_config_cache = None
_config_path = None

def init_db(app):
    """初始化配置模块"""
    global _config_path
    _config_path = app.config.get('CONFIG_PATH')
    
    # 如果配置文件不存在，创建默认配置
    if _config_path and not os.path.exists(_config_path):
        default_config = {
            "apiUrls": {},
            "baseTag": ""
        }
        with open(_config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)

def get_current_config():
    """获取当前配置"""
    global _config_cache, _config_path
    
    # 尝试从 Flask app 获取路径
    try:
        config_path = current_app.config.get('CONFIG_PATH', _config_path)
    except RuntimeError:
        config_path = _config_path
    
    if not config_path or not os.path.exists(config_path):
        return {"apiUrls": {}, "baseTag": ""}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"读取配置文件失败: {e}")
        return {"apiUrls": {}, "baseTag": ""}

def save_config(config):
    """保存配置到文件"""
    global _config_path
    
    try:
        config_path = current_app.config.get('CONFIG_PATH', _config_path)
    except RuntimeError:
        config_path = _config_path
    
    if not config_path:
        raise ValueError("配置文件路径未设置")
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except IOError as e:
        print(f"保存配置文件失败: {e}")
        return False

# =====================
# API 端点管理函数
# =====================

def get_all_api_endpoints():
    """获取所有 API 端点配置"""
    config = get_current_config()
    return config.get('apiUrls', {})

def add_api_endpoint(name, endpoint_config):
    """添加新的 API 端点
    
    Args:
        name: 端点名称（路由路径）
        endpoint_config: 端点配置字典
    
    Returns:
        bool: 成功返回 True，失败返回 False
    """
    config = get_current_config()
    
    if name in config.get('apiUrls', {}):
        return False  # 端点已存在
    
    if 'apiUrls' not in config:
        config['apiUrls'] = {}
    
    config['apiUrls'][name] = endpoint_config
    return save_config(config)

def update_api_endpoint(name, endpoint_config):
    """更新 API 端点配置
    
    Args:
        name: 端点名称
        endpoint_config: 新的端点配置
    
    Returns:
        bool: 成功返回 True，失败返回 False
    """
    config = get_current_config()
    
    if name not in config.get('apiUrls', {}):
        return False  # 端点不存在
    
    config['apiUrls'][name] = endpoint_config
    return save_config(config)

def delete_api_endpoint(name):
    """删除 API 端点
    
    Args:
        name: 端点名称
    
    Returns:
        bool: 成功返回 True，失败返回 False
    """
    config = get_current_config()
    
    if name not in config.get('apiUrls', {}):
        return False
    
    del config['apiUrls'][name]
    return save_config(config)

