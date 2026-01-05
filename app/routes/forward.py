"""
API 转发路由模块
处理 302 重定向和代理请求
"""
from flask import Blueprint, redirect, jsonify, request, abort
import requests
import re
from urllib.parse import urlencode, quote
from app.database import get_current_config
from app.storage import storage_manager

forward_bp = Blueprint('forward', __name__)

# 系统保留路径
RESERVED_PATHS = {'config', 'admin', 'admin-login', 'admin-logout', 'api', 
                  'css', 'js', 'picture', 'view', 'project_bg', 'static'}

def get_value_by_dot_notation(obj, path):
    """通过点号路径获取嵌套对象的值"""
    if not path:
        return None
    try:
        parts = path.split('.')
        current = obj
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current
    except:
        return None

def handle_proxy_request(target_url, proxy_settings):
    """处理代理请求"""
    try:
        print(f'[Proxy] Requesting: {target_url}')
        resp = requests.get(target_url, timeout=15)
        
        if resp.status_code >= 400:
            return jsonify(resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {'error': f'Target API error ({resp.status_code})'}), resp.status_code
        
        # 尝试提取图片 URL
        image_url = None
        if proxy_settings.get('imageUrlField') and resp.headers.get('content-type', '').startswith('application/json'):
            try:
                data = resp.json()
                image_url = get_value_by_dot_notation(data, proxy_settings['imageUrlField'])
            except:
                pass
        
        # 检查是否是有效的图片 URL
        if isinstance(image_url, str) and re.search(r'\.(jpeg|jpg|gif|png|webp|bmp|svg)', image_url, re.I):
            print(f'[Proxy] Redirecting to: {image_url}')
            return redirect(image_url)
        
        # 根据 fallback 设置返回
        fallback = proxy_settings.get('fallbackAction', 'returnJson')
        if fallback == 'error':
            return jsonify({'error': 'Could not extract image URL'}), 404
        
        # 返回原始 JSON
        try:
            return jsonify(resp.json())
        except:
            return resp.text, resp.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Proxy request timeout'}), 504
    except requests.exceptions.RequestException as e:
        print(f'[Proxy] Failed: {str(e)}')
        return jsonify({'error': 'Proxy setup failed'}), 500

def is_api_endpoint(path):
    """检查路径是否为配置的 API 端点"""
    config = get_current_config()
    return path in config.get('apiUrls', {})

def is_collection(path):
    """检查路径是否为图片合集"""
    return storage_manager.collection_exists(path)

@forward_bp.route('/<path:api_key>')
def forward_request(api_key):
    """动态 API 转发路由"""
    print(f'[Forward Debug] Received request for: /{api_key}')
    
    # 跳过静态文件和系统路由
    if '.' in api_key or api_key == 'favicon.ico' or api_key in RESERVED_PATHS:
        print(f'[Forward Debug] Skipping reserved path: {api_key}')
        abort(404)
    
    # 检查是否是 API 端点
    config = get_current_config()
    print(f'[Forward Debug] Config loaded, apiUrls keys: {list(config.get("apiUrls", {}).keys())}')
    
    config_entry = config.get('apiUrls', {}).get(api_key)
    print(f'[Forward Debug] Config entry for {api_key}: {config_entry}')
    
    # 如果不是 API 端点但是图片合集，跳过让 redirect_bp 处理
    if not config_entry:
        if is_collection(api_key):
            print(f'[Forward Debug] {api_key} is a collection, passing to redirect_bp')
            abort(404)  # 让其他路由处理
        print(f'[Forward Debug] {api_key} not found in config')
        abort(404)
    
    if not config_entry.get('method'):
        print(f'[Forward Debug] {api_key} has no method defined')
        abort(404)
    
    print(f'[Router] Handling /{api_key}')
    
    # 处理特殊 URL 构造
    url_construction = config_entry.get('urlConstruction')
    
    if url_construction == 'special_forward':
        url = request.args.get('url')
        field = request.args.get('field') or config_entry.get('proxySettings', {}).get('imageUrlFieldFromParamDefault') or 'url'
        if not url:
            return jsonify({'error': 'Missing url parameter'}), 400
        proxy_settings = {**config_entry.get('proxySettings', {}), 'imageUrlField': field}
        return handle_proxy_request(url, proxy_settings)
    
    if url_construction == 'special_pollinations':
        tags = request.args.get('tags')
        if not tags:
            return jsonify({'error': 'Missing tags parameter'}), 400
        base_tag = config.get('baseTag', '')
        model_name = config_entry.get('modelName', '')
        prompt_url = f"{config_entry.get('url', '')}{quote(tags)}%2c{base_tag}?&model={model_name}&nologo=true"
        return redirect(prompt_url)
    
    if url_construction == 'special_draw_redirect':
        tags = request.args.get('tags')
        query_params = config_entry.get('queryParams', [])
        default_model = next((p.get('defaultValue') for p in query_params if p.get('name') == 'model'), 'flux')
        model = request.args.get('model', default_model)
        if not tags:
            return jsonify({'error': 'Missing tags parameter'}), 400
        return redirect(f'/{model}?tags={quote(tags)}')
    
    # 通用处理
    validated_params = {}
    errors = []
    
    for param in config_entry.get('queryParams', []):
        name = param.get('name')
        value = request.args.get(name)
        
        if value is not None:
            valid_values = param.get('validValues')
            if valid_values and value not in valid_values:
                errors.append(f"Invalid value for '{name}'")
            else:
                validated_params[name] = value
        elif param.get('required'):
            errors.append(f"Missing required parameter: {name}")
        elif param.get('defaultValue') is not None:
            validated_params[name] = param['defaultValue']
    
    if errors:
        return jsonify({'error': 'Invalid parameters', 'details': errors}), 400
    
    target_url = config_entry.get('url', '')
    if not target_url:
        return jsonify({'error': 'Configuration URL missing'}), 500
    
    # 拼接查询参数
    if validated_params:
        separator = '&' if '?' in target_url else '?'
        target_url = f"{target_url}{separator}{urlencode(validated_params)}"
    
    print(f'[Router] Target: {target_url}')
    
    # 根据方法处理
    if config_entry.get('method') == 'proxy':
        return handle_proxy_request(target_url, config_entry.get('proxySettings', {}))
    
    # 默认重定向
    return redirect(target_url)
