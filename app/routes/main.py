from flask import Blueprint, render_template, abort, send_from_directory, current_app
from werkzeug.utils import safe_join
import os
from app.storage import storage_manager

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """主页：显示所有图片合集"""
    all_collection_names = storage_manager.get_all_collections()
    collections_with_info = []
    for name in all_collection_names:
        # 检查合集是否有内容（本地图片或外链）
        has_images = len(storage_manager.get_collection_images(name)) > 0
        has_links = len(storage_manager.get_collection_links(name)) > 0
        has_content = has_images or has_links
        collections_with_info.append({
            'name': name,
            'has_content': has_content
        })
    # 获取背景图片和透明度配置
    background_image_filename = current_app.config.get('BACKGROUND_IMAGE_PATH')
    background_opacity = current_app.config.get('BACKGROUND_OPACITY')
    
    return render_template('index.html',
                           collections=collections_with_info,
                           background_image_filename=background_image_filename,
                           background_opacity=background_opacity)

@main_bp.route('/view/<collection_name>')
def view_collection(collection_name):
    """查看特定合集的内容
    
    Args:
        collection_name: 合集名称
    """
    # 检查合集是否存在
    if not storage_manager.collection_exists(collection_name):
        abort(404)
    
    # 获取合集中的所有图片和外链
    images = storage_manager.get_collection_images(collection_name)
    links = storage_manager.get_collection_links(collection_name)
    
    # 构造图片URL
    image_urls = []
    for image in images:
        image_urls.append(f'/picture/{collection_name}/{image}')
    
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
    # 始终基于 app.root_path 构建路径
    if not os.path.isabs(picture_dir_name):
        # current_app.root_path is typically /app in the container
        directory = os.path.join(current_app.root_path, picture_dir_name)
    else:
        directory = picture_dir_name
    
    current_app.logger.debug(f"MainRoutes serve_picture: Serving '{filename}' from directory '{directory}'")
    return send_from_directory(directory, filename)

# 新增路由：用于服务项目根目录下存储的背景图片
@main_bp.route('/project_bg/<path:filename>')
def serve_project_background(filename):
    """提供项目 /app/background/ 目录下的背景图片文件服务"""
    # 背景图片存储在 /app/background/ (容器内)
    backgrounds_dir = os.path.join(current_app.root_path, 'background')
    
    # 使用 safe_join 确保路径安全，并检查文件是否存在
    safe_path = safe_join(backgrounds_dir, filename)
    
    if safe_path is None or not os.path.isfile(safe_path):
        current_app.logger.warning(f"Project background file not found or path is unsafe: '{filename}' in '{backgrounds_dir}'")
        abort(404)
        
    current_app.logger.debug(f"MainRoutes: Serving project background. Directory: '{backgrounds_dir}', Filename: '{filename}'")
    return send_from_directory(backgrounds_dir, filename)