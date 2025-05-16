from flask import Blueprint, send_file, redirect, abort
from app.storage import storage_manager

redirect_bp = Blueprint('redirect', __name__)

@redirect_bp.route('/<collection_name>')
def random_redirect(collection_name):
    """随机转发：从指定合集中随机返回一个图片资源
    
    Args:
        collection_name: 合集名称
    """
    # 检查合集是否存在
    if not storage_manager.collection_exists(collection_name):
        abort(404)
    
    # 从合集中随机获取一个资源
    resource_type, resource_path = storage_manager.get_random_resource(collection_name)
    
    if not resource_type or not resource_path:
        abort(404, description=f"合集 '{collection_name}' 中没有可用的资源")
    
    # 根据资源类型处理请求
    if resource_type == 'local':
        # 本地图片：直接返回文件
        return send_file(resource_path)
    elif resource_type == 'external':
        # 外部链接：通过HTTP重定向
        return redirect(resource_path)
    else:
        # 未知资源类型
        abort(500, description="系统错误：未知的资源类型")