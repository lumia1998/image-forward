from flask import Blueprint, render_template, abort, send_from_directory, current_app, jsonify, request
from werkzeug.utils import safe_join
import os
import time
from app.storage import storage_manager
from app.database import get_current_config

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """主页：显示所有图片合集和API端点"""
    # 获取背景图片和透明度配置
    background_image_filename = current_app.config.get('BACKGROUND_IMAGE_PATH')
    background_opacity = current_app.config.get('BACKGROUND_OPACITY')
    
    return render_template('index.html',
                           background_image_filename=background_image_filename,
                           background_opacity=background_opacity)

@main_bp.route('/api/homepage-data')
def homepage_data():
    """首页数据 API - 返回 LLM 提示词和卡片 HTML"""
    config = get_current_config()
    base_url = f"{request.scheme}://{request.host}"
    
    # 分组优先级
    group_order = {'AI绘图': 1, '二次元图片': 2, '三次元图片': 3, '表情包': 4, '默认分组': 99}
    
    # 按分组归类 API 端点
    grouped_apis = {}
    api_urls = config.get('apiUrls', {})
    
    for key, entry in api_urls.items():
        group = entry.get('group') or '默认分组'
        if group not in grouped_apis:
            grouped_apis[group] = []
        grouped_apis[group].append({'key': key, **entry})
    
    # 生成 LLM 提示词
    all_apis = [{'key': k, **v} for k, v in api_urls.items()]
    all_apis.sort(key=lambda x: (group_order.get(x.get('group', '默认分组'), 50), x['key']))
    
    # 添加图片合集到提示词
    collections = storage_manager.get_all_collections()
    
    path_functions = []
    for e in all_apis:
        desc = e.get('description') or e.get('group') or '默认分组'
        if e.get('group') == 'AI绘图':
            path_functions.append(f"{desc}:/{e['key']}?tags=<tags>")
        else:
            path_functions.append(f"{desc}:/{e['key']}")
    
    # 添加图片合集到路径列表
    for name in collections:
        info = storage_manager.get_collection_info(name)
        if info and info.get('has_content'):
            path_functions.append(f"本地图片合集-{name}:/{name}")
    
    llm_prompt = f"""    picture_url: |
    {{ 
    根据用户请求，选择合适的图片API路径，生成并返回完整URL。仅输出最终URL。
    基础URL：{base_url}
    可用路径：
{chr(10).join('    - ' + p for p in path_functions)}
    }}"""
    
    # 生成分组 HTML
    sorted_groups = sorted(grouped_apis.keys(), key=lambda x: group_order.get(x, 99))
    groups_html = ''
    timestamp = int(time.time() * 1000)
    
    for group_name in sorted_groups:
        endpoints = grouped_apis[group_name]
        endpoints.sort(key=lambda x: x['key'])
        
        cards_html = ''
        for entry in endpoints:
            api_url = f"{base_url}/{entry['key']}"
            desc = entry.get('description') or entry['key']
            cards_html += f'''
            <div class="api-card">
                <div class="api-card-image" onclick="refreshImage(this, '{api_url}')">
                    <div class="media-loader"><div class="loader-spinner"></div><span>加载中...</span></div>
                    <img src="{api_url}?t={timestamp}" alt="{desc}" loading="lazy" onload="hideLoader(this)" onerror="handleMediaError(this, '{api_url}')">
                    <div class="image-overlay"><span class="refresh-hint"><i class="bi bi-arrow-clockwise"></i> 点击刷新</span></div>
                    <span class="api-badge">{desc}</span>
                </div>
                <div class="api-card-info">
                    <p class="api-hint">👆点击图片可刷新预览</p>
                    <p class="api-url">{api_url}</p>
                </div>
            </div>'''
        
        groups_html += f'<div class="group-section"><h3 class="group-title-home">{group_name}</h3><div class="cards-row">{cards_html}</div></div>'
    
    # 生成图片合集 HTML
    collections_html = ''
    if collections:
        collection_cards = ''
        for name in collections:
            info = storage_manager.get_collection_info(name)
            if info and info.get('has_content'):
                collection_url = f"{base_url}/{name}"
                cover_url = f"{base_url}/picture/{name}/{info['cover']}" if info.get('cover') else ''
                count_text = f"{info.get('total_count', 0)} 张图片"
                
                if cover_url:
                    collection_cards += f'''
            <div class="api-card">
                <div class="api-card-image" onclick="refreshImage(this, '{collection_url}')">
                    <div class="media-loader"><div class="loader-spinner"></div><span>加载中...</span></div>
                    <img src="{cover_url}?t={timestamp}" alt="{name}" loading="lazy" onload="hideLoader(this)" onerror="handleMediaError(this, '{collection_url}')">
                    <div class="image-overlay"><span class="refresh-hint"><i class="bi bi-arrow-clockwise"></i> 点击刷新</span></div>
                    <span class="api-badge">{name}</span>
                </div>
                <div class="api-card-info">
                    <p class="api-hint">📁 {count_text}</p>
                    <p class="api-url">{collection_url}</p>
                </div>
            </div>'''
                else:
                    collection_cards += f'''
            <div class="api-card">
                <div class="api-card-image" onclick="refreshImage(this, '{collection_url}')">
                    <div class="media-loader"><div class="loader-spinner"></div><span>加载中...</span></div>
                    <img src="{collection_url}?t={timestamp}" alt="{name}" loading="lazy" onload="hideLoader(this)" onerror="handleMediaError(this, '{collection_url}')">
                    <div class="image-overlay"><span class="refresh-hint"><i class="bi bi-arrow-clockwise"></i> 点击刷新</span></div>
                    <span class="api-badge">{name}</span>
                </div>
                <div class="api-card-info">
                    <p class="api-hint">📁 {count_text}</p>
                    <p class="api-url">{collection_url}</p>
                </div>
            </div>'''
        
        if collection_cards:
            collections_html = f'<div class="group-section"><h3 class="group-title-home">📷 本地图片合集</h3><div class="cards-row">{collection_cards}</div></div>'
    
    return jsonify({
        'llmPrompt': llm_prompt,
        'groupsHtml': groups_html + collections_html
    })

@main_bp.route('/view/<collection_name>')
def view_collection(collection_name):
    """查看特定合集的内容"""
    if not storage_manager.collection_exists(collection_name):
        abort(404)
    
    images = storage_manager.get_collection_images(collection_name)
    links = storage_manager.get_collection_links(collection_name)
    
    image_urls = [f'/picture/{collection_name}/{image}' for image in images]
    
    return render_template(
        'collection.html',
        collection_name=collection_name,
        images=image_urls,
        links=links
    )

@main_bp.route('/picture/<path:filename>')
def serve_picture(filename):
    """提供图片文件服务"""
    picture_dir_name = current_app.config.get('PICTURE_DIR', 'picture')
    if not os.path.isabs(picture_dir_name):
        directory = os.path.join(current_app.root_path, picture_dir_name)
    else:
        directory = picture_dir_name
    
    current_app.logger.debug(f"MainRoutes serve_picture: Serving '{filename}' from directory '{directory}'")
    return send_from_directory(directory, filename)

@main_bp.route('/project_bg/<path:filename>')
def serve_project_background(filename):
    """提供项目背景图片文件服务"""
    backgrounds_dir = os.path.join(current_app.root_path, 'background')
    
    safe_path = safe_join(backgrounds_dir, filename)
    
    if safe_path is None or not os.path.isfile(safe_path):
        current_app.logger.warning(f"Project background file not found: '{filename}'")
        abort(404)
        
    return send_from_directory(backgrounds_dir, filename)
