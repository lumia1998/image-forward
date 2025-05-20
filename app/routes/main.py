from flask import Blueprint, render_template, abort, send_from_directory, current_app, safe_join
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
    # 获取背景图片和透明度配置
    # 假设主页使用与管理页相同的背景图片文件名配置键
    background_image_filename = current_app.config.get('BACKGROUND_IMAGE_PATH')
    background_opacity = current_app.config.get('BACKGROUND_OPACITY')
    
    return render_template('index.html',
                           collections=collections_with_covers,
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
    picture_dir = current_app.config.get('PICTURE_DIR')
    return send_from_directory(os.path.abspath(picture_dir), filename)

# 新增路由：用于服务项目根目录下存储的背景图片
@main_bp.route('/project_bg/<path:filename>')
def serve_project_background(filename):
    """提供项目根目录下特定子目录中的背景图片文件服务"""
    # 图片实际存储在宿主机的 d:/image-forward/project_backgrounds/
    # 假设该目录被映射到容器内的 /app/project_backgrounds/
    # current_app.root_path 指向 /app (如果 WORKDIR 是 /app)
    # 因此，背景图片目录是 /app/project_backgrounds
    backgrounds_dir = os.path.join(current_app.root_path, 'background')
    
    # 安全性：只允许服务配置中指定的背景图片文件名
    allowed_files = [
        current_app.config.get('BACKGROUND_LOGIN_IMAGE_PATH'),
        current_app.config.get('BACKGROUND_ADMIN_IMAGE_PATH')
    ]
    # 移除None值（如果配置项不存在或为空）
    allowed_files = [f for f in allowed_files if f]

    if filename in allowed_files:
        # 使用 safe_join 进一步确保路径安全
        safe_path = safe_join(backgrounds_dir, filename)
        if safe_path is None or not os.path.isfile(safe_path):
            current_app.logger.warning(f"Project background file not found or path is unsafe: {filename} in {backgrounds_dir}")
            abort(404)
        current_app.logger.debug(f"MainRoutes: Serving project background. Directory: {backgrounds_dir}, Filename: {filename}")
        return send_from_directory(backgrounds_dir, filename)
    else:
        current_app.logger.warning(f"Attempt to access non-allowed project background file: {filename}")
        abort(404)