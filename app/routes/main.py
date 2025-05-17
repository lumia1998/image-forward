from flask import Blueprint, render_template, abort, send_from_directory, current_app
import os
from app.storage import storage_manager

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """主页：显示所有图片合集"""
    all_collection_names = storage_manager.get_all_collections()
    collections_with_covers = []
    for name in all_collection_names:
        cover_filename = storage_manager.get_collection_cover_image_filename(name)
        cover_url = None
        if cover_filename:
            # 注意：这里的 URL 构造方式需要与 serve_picture 路由匹配
            # serve_picture 期望的 filename 是 'collection_name/image_filename.ext'
            cover_url = f'/picture/{name}/{cover_filename}'
        collections_with_covers.append({
            'name': name,
            'cover_url': cover_url
        })
    return render_template('index.html', collections=collections_with_covers)

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