from flask import Blueprint, render_template, abort, send_from_directory, current_app
import os
from app.storage import storage_manager

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """主页：显示所有图片合集"""
    collections = storage_manager.get_all_collections()
    return render_template('index.html', collections=collections)

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
    picture_dir = current_app.config.get('PICTURE_DIR')
    return send_from_directory(os.path.abspath(picture_dir), filename)