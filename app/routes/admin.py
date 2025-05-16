from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app, send_from_directory
from app.storage import storage_manager
from app.auth.auth import login, logout, login_required
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
def index():
    """管理页：显示所有图片合集"""
    collections = storage_manager.get_all_collections()
    return render_template('admin.html', collections=collections)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    """登录页面"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        
        if login(password):
            return redirect(url_for('admin.index'))
        else:
            flash('密码错误！', 'danger')
    
    return render_template('login.html')

@admin_bp.route('/logout')
def logout_action():
    """登出操作"""
    logout()
    return redirect(url_for('admin.login_page'))

@admin_bp.route('/collection/create', methods=['POST'])
@login_required
def create_collection():
    """创建新的合集"""
    collection_name = request.form.get('collection_name', '').strip()
    
    if not collection_name:
        flash('合集名称不能为空！', 'danger')
        return redirect(url_for('admin.index'))
    
    # 检查合集名称是否合法（不包含特殊字符）
    if not collection_name.isalnum() and collection_name != '_':
        flash('合集名称只能包含字母、数字和下划线！', 'danger')
        return redirect(url_for('admin.index'))
    
    result = storage_manager.create_collection(collection_name)
    
    if result:
        flash(f'合集 "{collection_name}" 创建成功！', 'success')
    else:
        flash(f'合集 "{collection_name}" 已存在！', 'warning')
    
    return redirect(url_for('admin.index'))

@admin_bp.route('/collection/delete', methods=['POST'])
@login_required
def delete_collection():
    """删除合集"""
    collection_name = request.form.get('collection_name', '')
    
    if not collection_name:
        flash('参数错误！', 'danger')
        return redirect(url_for('admin.index'))
    
    result = storage_manager.delete_collection(collection_name)
    
    if result:
        flash(f'合集 "{collection_name}" 删除成功！', 'success')
    else:
        flash(f'删除合集 "{collection_name}" 失败！', 'danger')
    
    return redirect(url_for('admin.index'))

@admin_bp.route('/collection/<collection_name>')
@login_required
def manage_collection(collection_name):
    """管理指定合集"""
    if not storage_manager.collection_exists(collection_name):
        abort(404)
    
    images = storage_manager.get_collection_images(collection_name)
    links = storage_manager.get_collection_links(collection_name)
    
    # 构造图片URL
    image_urls = []
    for image in images:
        image_urls.append({
            'name': image,
            'url': f'/picture/{collection_name}/{image}'
        })
    
    return render_template(
        'manage_collection.html',
        collection_name=collection_name,
        images=image_urls,
        links=links
    )

@admin_bp.route('/collection/<collection_name>/upload', methods=['POST'])
@login_required
def upload_image(collection_name):
    """上传图片到合集"""
    if not storage_manager.collection_exists(collection_name):
        abort(404)
    
    # 检查是否有文件上传
    if 'image' not in request.files:
        flash('没有上传文件！', 'danger')
        return redirect(url_for('admin.manage_collection', collection_name=collection_name))
    
    file = request.files['image']
    
    # 检查文件名是否为空
    if file.filename == '':
        flash('没有选择文件！', 'danger')
        return redirect(url_for('admin.manage_collection', collection_name=collection_name))
    
    # 上传文件
    filename = storage_manager.add_image_to_collection(collection_name, file)
    
    if filename:
        flash(f'图片 "{filename}" 上传成功！', 'success')
    else:
        flash('图片上传失败！', 'danger')
    
    return redirect(url_for('admin.manage_collection', collection_name=collection_name))

@admin_bp.route('/collection/<collection_name>/add-links', methods=['POST'])
@login_required
def add_links(collection_name):
    """添加外链到合集"""
    if not storage_manager.collection_exists(collection_name):
        abort(404)
    
    links_text = request.form.get('links', '')
    
    if not links_text.strip():
        flash('请输入至少一个外链！', 'warning')
        return redirect(url_for('admin.manage_collection', collection_name=collection_name))
    
    # 分割文本为链接列表
    links = [link.strip() for link in links_text.split('\n') if link.strip()]
    
    # 验证链接
    valid_links = []
    for link in links:
        if link.startswith(('http://', 'https://')):
            valid_links.append(link)
    
    if not valid_links:
        flash('没有有效的外链！所有链接必须以http://或https://开头。', 'warning')
        return redirect(url_for('admin.manage_collection', collection_name=collection_name))
    
    count = storage_manager.add_links_to_collection(collection_name, valid_links)
    
    flash(f'成功添加 {count} 个外链！', 'success')
    return redirect(url_for('admin.manage_collection', collection_name=collection_name))

@admin_bp.route('/collection/<collection_name>/delete-image', methods=['POST'])
@login_required
def delete_image(collection_name):
    """从合集中删除图片"""
    if not storage_manager.collection_exists(collection_name):
        abort(404)
    
    image_name = request.form.get('image_name', '')
    
    if not image_name:
        flash('参数错误！', 'danger')
        return redirect(url_for('admin.manage_collection', collection_name=collection_name))
    
    result = storage_manager.delete_image_from_collection(collection_name, image_name)
    
    if result:
        flash(f'图片 "{image_name}" 删除成功！', 'success')
    else:
        flash(f'删除图片 "{image_name}" 失败！', 'danger')
    
    return redirect(url_for('admin.manage_collection', collection_name=collection_name))

@admin_bp.route('/collection/<collection_name>/delete-link', methods=['POST'])
@login_required
def delete_link(collection_name):
    """从合集中删除外链"""
    if not storage_manager.collection_exists(collection_name):
        abort(404)
    
    link = request.form.get('link', '')
    
    if not link:
        flash('参数错误！', 'danger')
        return redirect(url_for('admin.manage_collection', collection_name=collection_name))
    
    result = storage_manager.delete_link_from_collection(collection_name, link)
    
    if result:
        flash('外链删除成功！', 'success')
    else:
        flash('删除外链失败！', 'danger')
    
    return redirect(url_for('admin.manage_collection', collection_name=collection_name))

# 静态文件服务（图片文件）
@admin_bp.route('/picture/<path:filename>')
def serve_picture(filename):
    """提供图片文件服务"""
    picture_dir = current_app.config.get('PICTURE_DIR')
    return send_from_directory(os.path.abspath(picture_dir), filename)